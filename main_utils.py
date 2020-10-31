import os, shutil
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import re
import configparser
from termcolor import colored
from functools import wraps
import time
from main_classes import Company

ENCODING='utf8'

config = configparser.RawConfigParser()
config.read('config_file.ini',encoding=ENCODING)
webs_to_scrapp=config['DEFAULT']['webs_to_scrapp']
articles_path=config['DEFAULT']['articles_path']
SEPARATOR=config['DEFAULT']['separator']

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
  folder_cleaner()
  companies=web_searcher()
  s = requests.session()
  for company in companies:
    web=company.website
    r = s.get(web)
    soup = BeautifulSoup(r.text, 'html.parser')
    web_content=soup.find('body').text
    web_conten_after_cleaner=text_cleaner(web_content)
    articles_to_txt(company,web_conten_after_cleaner)

def web_searcher():
  companies=[]
  df=pd.read_csv('{}'.format(webs_to_scrapp), sep=SEPARATOR,encoding=ENCODING)
  for index, row in df.iterrows():
    company=Company(row['Name'],row['Web'],row['Type'])
    companies.append(company)
  return companies

def articles_to_txt(company,content):
  with open("{}{}{}".format(articles_path,company.name,'.txt'), "w") as text_file:
    text_file.write(content)

def folder_cleaner():
  for filename in os.listdir(articles_path):
      file_path = os.path.join(articles_path, filename)
      try:
          if os.path.isfile(file_path) or os.path.islink(file_path):
              os.unlink(file_path)
          elif os.path.isdir(file_path):
              shutil.rmtree(file_path)
      except Exception as e:
          print('Failed to delete %s. Reason: %s' % (file_path, e))

web_crawler()