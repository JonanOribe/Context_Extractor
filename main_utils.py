import os, shutil
import requests
import pandas as pd
import re
import configparser
import operator
from memory_profiler import profile
from bs4 import BeautifulSoup
from termcolor import colored
from functools import wraps
from time import time
import asyncio
from timeit import default_timer
from aiohttp import ClientSession
from main_classes import Company

ENCODING='utf8'
diccionaries_len_arr=[]

config = configparser.RawConfigParser()
config.read('config_file.ini',encoding=ENCODING)
webs_to_scrapp=config['DEFAULT']['webs_to_scrapp']
articles_path=config['DEFAULT']['articles_path']
dictionaries_path=config['DEFAULT']['dictionaries_path']
macro_dictionaries_path=config['DEFAULT']['macro_dictionaries_path']
SEPARATOR=config['DEFAULT']['separator']
max_len=int(config['DEFAULT']['max_len'])
min_len=int(config['DEFAULT']['min_len'])
max_character_per_article_spacy=int(config['DEFAULT']['max_character_per_article_spacy'])
file_type=config['DEFAULT']['file_type']
dictionaries_range_for_discard=float(config['DEFAULT']['dictionaries_range_for_discard'])
quantile=float(config['DEFAULT']['quantile'])
arr_points_percent=config['DEFAULT']['arr_points_percent'].split(',')
arr_points_percent=list(map(lambda x: int(x), arr_points_percent))

arr_paths=[articles_path,dictionaries_path,macro_dictionaries_path]
web_type_and_url_dict={}
not_async_web_dict=[]


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print (colored('>>> Func:%r took: %2.4f sec' % \
          (f.__name__, te-ts),'green'))
        return result
    return wrap

def asterisks(num):
    """Returns a string of asterisks reflecting the magnitude of a number."""
    return int(num*10)*'*'

async def fetch(company, session):
    """Fetch a url, using specified ClientSession."""
    print(company.description())
    url=company.website
    fetch.start_time[url] = default_timer()
    try:
      async with session.get(url) as response:
          resp = await response.read()
          website_info_getter_and_cleaner(session,company,resp)
          elapsed = default_timer() - fetch.start_time[url]
          print('{0:30}{1:5.2f} {2}'.format(url, elapsed, asterisks(elapsed)))
          return resp
    except Exception as e:
      print( colored("<p>Error: %s</p>" % str(e),'red'))
      not_async_web_dict.append(company)

async def fetch_all(companies):
    """Launch requests for all web pages."""
    tasks = []
    fetch.start_time = dict() # dictionary of start times for each url
    async with ClientSession() as session:
        for company in companies:
            task = asyncio.ensure_future(fetch(company, session))
            tasks.append(task) # create list of tasks
        _ = await asyncio.gather(*tasks) # gather task responses

def text_cleaner(web_content):
  #regex = re.compile(r"(<\/\w*>|<\w*>|<\w*|\".*\"|\w*=|'.*')|([^a-zA-Z])")
  regex = re.compile('[^a-zA-Z]')
  return regex.sub(' ', web_content)

def website_info_getter_and_cleaner(session,company,text):
  try:
    if(text=='empty'):
      text = session.get(company.website).text
    soup = BeautifulSoup(text, 'html.parser')
    web_conten_after_cleaner=text_cleaner(soup.find('body').text)
    articles_to_txt(company,web_conten_after_cleaner)
  except:
    pass

def crawler_async(session,companies):
    """Fetch list of web pages asynchronously."""
    start_time = default_timer()

    loop = asyncio.get_event_loop() # event loop
    future = asyncio.ensure_future(fetch_all(companies)) # tasks to do
    loop.run_until_complete(future) # loop until done

    tot_elapsed = default_timer() - start_time
    print(colored(' WITH ASYNCIO: '.rjust(30, '-') + '{0:5.2f} {1}'. \
        format(tot_elapsed, asterisks(tot_elapsed)),'green'))
    if(len(not_async_web_dict)>0):
      resp='empty'
      [website_info_getter_and_cleaner(session,company,resp) for company in not_async_web_dict]

@timing
def web_crawler():
  session = requests.session()
  [folder_cleaner(x) for x in arr_paths]
  #map(lambda x: folder_cleaner(x), arr_paths)
  print(colored('This will took a while...','yellow'))
  companies=web_searcher()
  crawler_async(session,companies)

@timing
def web_searcher():
  companies=[]
  df=pd.read_csv('{}'.format(webs_to_scrapp), sep=SEPARATOR,encoding=ENCODING)
  [companies.append(Company(row['Name'],row['Web'],row['Type'])) for index, row in df.iterrows()]
  return companies

def articles_to_txt(company,content):
  with open("{}{}{}{}{}".format(articles_path,company.type,'_',company.name,'.txt'), "w") as text_file:
    text_file.write(content)

@timing
def folder_cleaner(articles_path):
  for filename in os.listdir(articles_path):
      file_path = os.path.join(articles_path, filename)
      try:
          if os.path.isfile(file_path) or os.path.islink(file_path):
              os.unlink(file_path)
          elif os.path.isdir(file_path):
              shutil.rmtree(file_path)
      except Exception as e:
          print('Failed to delete %s. Reason: %s' % (file_path, e))

#@timing
def words_classification(doc,words_dict):
  for token in doc:
    if(token.pos_=="NOUN" and max_len>len(token)>min_len and token.lemma_.isnumeric()==False):
            word=token.lemma_.lower()
            if word in words_dict.keys():
                words_dict[word]=words_dict[word]+1
            else:
                words_dict[word]=1
  return words_dict

def points_distribution(df_len,points_list):
  ranges=[]
  ranges.append(range(0,points_list[0]))
  ranges.append(range(points_list[0], points_list[1]))
  ranges.append(range(points_list[1], points_list[2]))
  ranges.append(range(points_list[2],df_len))
  return ranges

def dataframe_percent_and_points(df_len):
  return points_distribution(df_len,list(map(lambda x: round((df_len/100)*x), arr_points_percent)))

def df_words_clustering_by_percent(df):
  return dataframe_percent_and_points(len(df))

@timing
def macro_dictionaries_filter(number_of_dicts,macro_df):
  #How many times a word can appear in the dictionaries before being discarded
  top_count=number_of_dicts-(round(number_of_dicts/dictionaries_range_for_discard))

  macro_df_with_filter=macro_df[macro_df.Count < top_count]
  macro_df_with_filter=macro_df_with_filter.sort_values(by='Word', ascending=True)
  macro_dict_with_words_out_of_bounds=macro_df[macro_df.Count >= top_count]

  macro_df_with_filter.to_csv('{}{}{}'.format(macro_dictionaries_path,'macro-dictionary',file_type),sep=SEPARATOR,encoding=ENCODING,index=False)
  macro_dict_with_words_out_of_bounds.to_csv('{}{}{}'.format(macro_dictionaries_path,'macro-dictionary-out-of-bounds',file_type),sep=SEPARATOR,encoding=ENCODING,index=False)

  micro_dictionaries=set_micro_dictionaries(min_len,macro_df_with_filter)
  #Cleaning data with words out of bounds
  return macro_dict_with_words_out_of_bounds['Word'].array,micro_dictionaries,macro_df_with_filter

def dictionaries_cleaner_by_quantile(dictionaries_path):
  for r, d, f in os.walk(dictionaries_path):
    for file in f:
      df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
      df=df[df.Total > df['Total'].quantile(quantile)]
      df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

def articles_len_filter(article):
  return article if(len(article)<max_character_per_article_spacy) else article[:max_character_per_article_spacy]

@timing
#@profile
def predict_new_website_context(nlp,micro_dictionaries,macro_df_with_filter):
  session = requests.session()
  arr_to_predict=[
    'https://hbase.apache.org/'
    ,'https://aws.amazon.com/'
    ,'https://en.wikipedia.org/wiki/Tupolev'
    ,'https://en.wikipedia.org/wiki/Tesla,_Inc.'
    ,'https://www.tesla.com/modelx'
    ,'https://www.tesla.com/modely'
    ,'https://en.wikipedia.org/wiki/SolarCity'
    ,'https://explained.ai/'
    ,'https://bl.ocks.org/mbostock'
    ]
  for url in arr_to_predict:
    final_result_dict={}
    words_dict_candidate={}
    r = session.get(url)
    candidate_text=text_cleaner(r.text)
    words_classification(nlp(candidate_text),words_dict_candidate)

    df_from_candidate = pd.DataFrame()
    df_from_candidate['Word']=words_dict_candidate.keys()
    df_from_candidate['Count']=words_dict_candidate.values()

    for r, d, f in os.walk(dictionaries_path):
        for file in f:
            count=points=0
            df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
            df_words_keys,df_words=get_df_keys(df)
            for index, row in df_from_candidate.iterrows():
              filtered_section=row['Word'][:min_len]
              try:
                current_section_of_dictionary=macro_df_with_filter[micro_dictionaries[filtered_section+'--Begin']:micro_dictionaries[filtered_section+'--End']+1]
                df_temp_for_scorer=current_section_of_dictionary[current_section_of_dictionary['Word'] == row['Word']]
                if(len(df_temp_for_scorer)>0) and (row['Word'] in df_words_keys):
                    points=points+df_words[row['Word']]
                    count=count+1
              except BaseException as error:
                #print(error)
                continue
            final_result_dict[file.split(file_type)[0].title()]=points
        final_result_dict=sorted(final_result_dict.items(), key=operator.itemgetter(1), reverse=True)
        print('{}{}'.format(colored(url,'yellow'),colored(final_result_dict, 'green')))

def reduce_dictionaries_to_smallest_one(dictionaries_len_dict):
  SMALLEST_DICTIONARY_LEN = dictionaries_len_dict[min(dictionaries_len_dict, key=dictionaries_len_dict.get)]
  print('{}{}'.format(colored('SMALLEST_DICTIONARY: ','yellow'),colored(SMALLEST_DICTIONARY_LEN, 'green')))
  for r, d, f in os.walk(dictionaries_path):
      for file in f:
          df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
          df=df[:SMALLEST_DICTIONARY_LEN]
          df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

def set_micro_dictionaries(chunk_size,df):
    first_chars={}
    counter=0
    for index, row in df.iterrows():
        filter_section=row['Word'][:chunk_size]
        if not ((filter_section+'--Begin') in first_chars.keys()):
            first_chars[filter_section+'--Begin']=counter
        else:
            first_chars[filter_section+'--End']=counter
        counter+=1
    return first_chars

def get_df_keys(df):
  df_words={}
  for index, row in df.iterrows():
    df_words[row['Word']]=row['Points']
  return df_words.keys(),df_words
