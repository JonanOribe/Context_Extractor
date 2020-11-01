import os, shutil
import requests
import pandas as pd
import re
import configparser
from bs4 import BeautifulSoup
from termcolor import colored
from functools import wraps
from time import time
from main_classes import Company

ENCODING='utf8'

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

def text_cleaner(web_content):
  #regex = re.compile(r"(<\/\w*>|<\w*>|<\w*|\".*\"|\w*=|'.*')|([^a-zA-Z])")
  regex = re.compile('[^a-zA-Z]')
  return regex.sub(' ', web_content)

def website_info_getter_and_cleaner(session,company):
    r = session.get(company.website)
    soup = BeautifulSoup(r.text, 'html.parser')
    web_conten_after_cleaner=text_cleaner(soup.find('body').text)
    articles_to_txt(company,web_conten_after_cleaner)

@timing
def web_crawler():
  session = requests.session()
  map(lambda x: folder_cleaner(x), arr_paths)
  print(colored('This will took a while...','yellow'))
  [website_info_getter_and_cleaner(session,company) for company in web_searcher()]

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

@timing
def words_classification(doc,words_dict):
  for token in doc:
    if(token.pos_=="NOUN" and max_len>len(token)>min_len and token.text.isnumeric()==False):
            word=token.text.lower()
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
  macro_dict_with_words_out_of_bounds=macro_df[macro_df.Count >= top_count]

  macro_df_with_filter.to_csv('{}{}{}'.format(macro_dictionaries_path,'macro-dictionary',file_type),sep=SEPARATOR,encoding=ENCODING,index=False)
  macro_dict_with_words_out_of_bounds.to_csv('{}{}{}'.format(macro_dictionaries_path,'macro-dictionary-out-of-bounds',file_type),sep=SEPARATOR,encoding=ENCODING,index=False)
  #Cleaning data with words out of bounds
  return macro_dict_with_words_out_of_bounds['Word'].array

def dictionaries_cleaner_by_quantile(dictionaries_path):
  for r, d, f in os.walk(dictionaries_path):
    for file in f:
      df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
      df=df[df.Total > df['Total'].quantile(quantile)]
      df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

def articles_len_filter(article):
  return article if(len(article)<max_character_per_article_spacy) else article[:max_character_per_article_spacy]