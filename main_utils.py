import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import re
import configparser
from termcolor import colored
from functools import wraps
import time

ENCODING='utf8'
SEPARATOR=';'

config = configparser.RawConfigParser()
config.read('config_file.ini',encoding=ENCODING)
webs_to_scrapp=config['DEFAULT']['webs_to_scrapp']
articles_path=config['DEFAULT']['articles_path']

web_type_and_url_dict={}

def text_cleaner(web_content):
  regex = re.compile('[^a-zA-Z]')
  output = regex.sub(' ', web_content)
  return output

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print ('func:%r args:[%r, %r] took: %2.4f sec' % \
          (f.__name__, args, kw, te-ts))
        return result
    return wrap

def web_crawler():
  articles_dict=web_searcher()
  s = requests.session()
  for web in articles_dict.keys():
    r = s.get(web)
    soup = BeautifulSoup(r.text, 'html.parser')
    web_content=soup.find('body').text
    web_conten_after_cleaner=text_cleaner(web_content)
    articles_to_txt(web,web_conten_after_cleaner)

def web_searcher():
  df=pd.read_csv('{}'.format(webs_to_scrapp), sep=SEPARATOR,encoding=ENCODING)
  for index, row in df.iterrows():
    web_type_and_url_dict[row['Web']]=row['Type']
  return web_type_and_url_dict

def articles_to_txt(web,content):
  with open("{}{}{}".format(articles_path,web,'.txt'), "w") as text_file:
    text_file.write(content)

web_crawler()