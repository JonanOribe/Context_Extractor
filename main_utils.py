import os, shutil
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import re
import configparser
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

@timing
def text_cleaner(web_content):
  regex = re.compile('[^a-zA-Z]')
  output = regex.sub(' ', web_content)
  return output

@timing
def web_crawler():
  folder_cleaner(articles_path)
  folder_cleaner(dictionaries_path)
  folder_cleaner(macro_dictionaries_path)
  companies=web_searcher()
  s = requests.session()
  for company in companies:
    web=company.website
    r = s.get(web)
    soup = BeautifulSoup(r.text, 'html.parser')
    web_content=soup.find('body').text
    web_conten_after_cleaner=text_cleaner(web_content)
    articles_to_txt(company,web_conten_after_cleaner)

@timing
def web_searcher():
  companies=[]
  df=pd.read_csv('{}'.format(webs_to_scrapp), sep=SEPARATOR,encoding=ENCODING)
  for index, row in df.iterrows():
    company=Company(row['Name'],row['Web'],row['Type'])
    companies.append(company)
  return companies

@timing
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
            dict_keys=words_dict.keys()
            if word in dict_keys:
                words_dict[word]=words_dict[word]+1
            else:
                words_dict[word]=1
  return words_dict