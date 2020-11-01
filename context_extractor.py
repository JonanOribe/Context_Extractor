import os
import pandas as pd
import spacy
import requests
import configparser
import operator
from pathlib import Path
from termcolor import colored
from spacy.lang.es.examples import sentences
from main_utils import df_words_clustering_by_percent, dictionaries_cleaner_by_quantile, macro_dictionaries_filter, text_cleaner, web_crawler, words_classification

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

final_result_dict={}
macroDictionary_dict={}
words_dict_candidate={}
macroDictionary=[]
number_of_dicts=0

#Launch crawler
web_crawler()

for r, d, f in os.walk(articles_path):
    for file in f:
        words_dict={}
        category_type=file.split('_')[0]
        dictionary_file='{}{}'.format(category_type,file_type)
        articleFile = open('{}{}{}'.format(r,'/',file),'r',encoding=ENCODING)
        article=articleFile.read()

        doc=nlp(article)

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
    number_of_dicts=len(f)
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

out_of_bounds=macro_dictionaries_filter(number_of_dicts,Macro_df)

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)

        for index, row in df.iterrows():
            if row['Word'] in out_of_bounds:
                df.drop([index], inplace=True)

        df.sort_values(by=['Total'], ascending=False,inplace=True)
        df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

#SORTING THE DATA BY COUNTS AND Adding weigths

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        df['Points']=0
        arr_points=[]
        first_range,second_range,third_range,last_range=df_words_clustering_by_percent(df)

        for index, row in df.iterrows():
            if index in first_range:
                arr_points.append(arr_points_values[0])
            if index in second_range:
                arr_points.append(arr_points_values[1])
            if index in third_range:
                arr_points.append(arr_points_values[2])
            if index in last_range:
                arr_points.append(arr_points_values[3])
        df['Points']=arr_points
        df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

#Crawling the candidate URL
#r = requests.get('https://www.nissan.es/experiencia-nissan.html')
#r = requests.get('http://www.x-plane.es/')
#r = requests.get('https://www.milanuncios.com/barcos-a-motor-en-vizcaya/')
#r = requests.get('https://www.cosasdebarcos.com/barcos-ocasion/en-vizcaya-49/')
#r = requests.get('https://www.google.com/intl/es_ALL/drive/using-drive/')
#r = requests.get('https://www.cosasdebarcos.com/empresas-nauticas-tienda-nautica-6/en-vizcaya-49/')
r = requests.get('https://www.ford.es/')
#r = requests.get('https://www.mi.com/es')

candidate_text=text_cleaner(r.text)

doc_candidate=nlp(candidate_text)

words_classification(doc_candidate,words_dict_candidate)

df_from_candidate = pd.DataFrame()
df_from_candidate['Word']=words_dict_candidate.keys()
df_from_candidate['Count']=words_dict_candidate.values()

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        count=points=0
        df_words={}
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        for index, row in df.iterrows():
            df_words[row['Word']]=row['Points']
        df_words_keys=df_words.keys()
        for index, row in df_from_candidate.iterrows():
            if row['Word'] in df_words_keys:
                points=points+df_words[row['Word']]
                count=count+1
        final_result_dict[file.split(file_type)[0].title()]=points
    final_result_dict=sorted(final_result_dict.items(), key=operator.itemgetter(1), reverse=True)
    print(colored(final_result_dict, 'green'))