import os
import pandas as pd
import spacy
import requests
import configparser
import operator
from pathlib import Path
from termcolor import colored
from spacy.lang.es.examples import sentences
from main_utils import articles_len_filter, df_words_clustering_by_percent, dictionaries_cleaner_by_quantile, macro_dictionaries_filter, predict_new_website_context, text_cleaner, web_crawler, words_classification

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

ENCODING='utf8'

config = configparser.RawConfigParser()
config.read('config_file.ini',encoding=ENCODING)
nlp = spacy.load('en_core_web_sm')

SEPARATOR=config['DEFAULT']['separator']
dictionaries_path=config['DEFAULT']['dictionaries_path']
articles_path = config['DEFAULT']['articles_path']
macro_dictionaries_path = config['DEFAULT']['macro_dictionaries_path']
file_type=config['DEFAULT']['file_type']
arr_points_values=config['DEFAULT']['arr_points'].split(',')

arr_points_values=list(map(lambda x: int(x), arr_points_values))

macroDictionary_dict={}
macroDictionary=[]

#Launch crawler
web_crawler()

for r, d, f in os.walk(articles_path):
    for file in f:
        words_dict={}
        category_type=file.split('_')[0]
        dictionary_file='{}{}'.format(category_type,file_type)
        articleFile = open('{}{}{}'.format(r,'/',file),'r',encoding=ENCODING)
        article=articleFile.read()

        doc=nlp(articles_len_filter(article))

        words_dict=words_classification(doc,words_dict)

        df_temp = pd.DataFrame()
        df_temp['Word']=words_dict.keys()
        df_temp['Count']=words_dict.values()
        file_path = Path('{}{}'.format(dictionaries_path,dictionary_file))
        if file_path.is_file():
            df=pd.read_csv('{}{}'.format(dictionaries_path,dictionary_file),sep=SEPARATOR)
            df_temp=df_temp.append(df, ignore_index=True)

        df_temp.to_csv('{}{}'.format(dictionaries_path,dictionary_file),sep=SEPARATOR,encoding=ENCODING,index=False)

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df_temp=pd.read_csv('{}{}'.format(dictionaries_path,file),sep=SEPARATOR)
        df_temp['Total']=df_temp.groupby(['Word'])['Count'].transform('sum')
        del df_temp['Count']
        df_temp=df_temp.drop_duplicates(keep = 'first')
        df_temp=df_temp.sort_values(by='Total',ascending=False)
        df_temp.to_csv('{}{}'.format(dictionaries_path,file),sep=SEPARATOR,encoding=ENCODING,index=False)

#Cleaning data
dictionaries_cleaner_by_quantile(dictionaries_path)

#Filter common words between dictionaries

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        for index, row in df.iterrows():
            word=row['Word']
            macroDict_keys=macroDictionary_dict.keys()
            if word in macroDict_keys:
                macroDictionary_dict[word]=macroDictionary_dict[word]+1
            else:
                macroDictionary_dict[word]=1
        Macro_df = pd.DataFrame()
        Macro_df['Word']=macroDictionary_dict.keys()
        Macro_df['Count']=macroDictionary_dict.values()

out_of_bounds=macro_dictionaries_filter(len(f),Macro_df)

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)

        for index, row in df.iterrows():
            if row['Word'] in out_of_bounds: df.drop([index], inplace=True)

        df.sort_values(by=['Total'], ascending=False,inplace=True)
        df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

#SORTING THE DATA BY COUNTS AND Adding weigths

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        df['Points']=0
        arr_points=[]
        ranges=df_words_clustering_by_percent(df)

        for index, row in df.iterrows():
            if index in ranges[0]: arr_points.append(arr_points_values[0])
            if index in ranges[1]: arr_points.append(arr_points_values[1])
            if index in ranges[2]: arr_points.append(arr_points_values[2])
            if index in ranges[3]: arr_points.append(arr_points_values[3])

        df['Points']=arr_points
        df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

predict_new_website_context(nlp)