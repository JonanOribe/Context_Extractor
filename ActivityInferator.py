import os
import pandas as pd
import spacy
import requests
import configparser
import operator
from pathlib import Path
from termcolor import colored
from spacy.lang.es.examples import sentences
from main_utils import web_crawler

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

ENCODING='utf8'

config = configparser.RawConfigParser()
config.read('config_file.ini',encoding=ENCODING)
nlp = spacy.load('en_core_web_sm')
arr_points_values=[12,8,6,2]
ENCODING='utf8'
SEPARATOR=config['DEFAULT']['separator']

config = configparser.RawConfigParser()
config.read('config_file.ini',encoding=ENCODING)
dictionaries_path=config['DEFAULT']['dictionaries_path']
articles_path = config['DEFAULT']['articles_path']
final_result_dict={}

#Launch crawler
web_crawler()

for r, d, f in os.walk(articles_path):
    for file in f:
        words_dict={}
        file_type=file.split('_')[0]
        dictionary_file=file_type+'.csv'
        articleFile = open('{}{}{}'.format(r,'/',file),'r',encoding=ENCODING)
        article=articleFile.read()

        doc=nlp(article)

        for token in doc:
            if(token.pos_=="NOUN" and 24>len(token)>1 and token.text.isnumeric()==False):
                word=token.text.lower()
                dict_keys=words_dict.keys()
                if word in dict_keys:
                    words_dict[word]=words_dict[word]+1
                else:
                    words_dict[word]=1
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
for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        quantile=df['Total'].quantile(.8)
        df=df[df.Total > quantile]
        df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

#Filter common words between dictionaries
macroDictionary=[]
macroDictionary_dict={}
number_of_dicts=0

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

#How many times a word can appear in the dictionaries before being discarded
top_count=number_of_dicts-(round(number_of_dicts/1.6))

Macro_df_with_filter=Macro_df[Macro_df.Count < top_count]
MacroDict_with_words_out_of_bounds=Macro_df[Macro_df.Count >= top_count]

print('Discarded words:')
print(MacroDict_with_words_out_of_bounds)
Macro_df_with_filter.to_csv('./macro-dictionary/macro-dictionary.csv',sep=SEPARATOR,encoding=ENCODING,index=False)
MacroDict_with_words_out_of_bounds.to_csv('./macro-dictionary/macro-dictionary-out-of-bounds.csv',sep=SEPARATOR,encoding=ENCODING,index=False)

#Cleaning data with words out of bounds
out_of_bounds=MacroDict_with_words_out_of_bounds['Word'].array

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)

        for index, row in df.iterrows():
            if row['Word'] in out_of_bounds:
                df.drop([index], inplace=True)

        df.sort_values(by=['Count'], ascending=False,inplace=True)
        df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

#SORTING THE DATA BY COUNTS AND Adding weigths

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        df['Points']=0
        arr_points=[]
        df_len=len(df)
        df_top_10_percent=round((df_len/100)*10)
        df_top_20_percent=round((df_len/100)*20)
        df_top_30_percent=round((df_len/100)*30)
        first_range=range(0,df_top_10_percent)
        second_range=range(df_top_10_percent, df_top_20_percent)
        third_range=range(df_top_20_percent, df_top_30_percent)
        last_range=range(df_top_30_percent,df_len)

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
r = requests.get('http://www.x-plane.es/')
#r = requests.get('https://www.milanuncios.com/barcos-a-motor-en-vizcaya/')
#r = requests.get('https://www.cosasdebarcos.com/barcos-ocasion/en-vizcaya-49/')
#r = requests.get('https://www.google.com/intl/es_ALL/drive/using-drive/')
#r = requests.get('https://www.cosasdebarcos.com/empresas-nauticas-tienda-nautica-6/en-vizcaya-49/')
#r = requests.get('https://www.ford.es/')
#r = requests.get('https://www.mi.com/es')

candidate_text=r.text

doc_candidate=nlp(candidate_text)

words_dict_candidate={}

for token in doc_candidate:
    if('/' not in token.text and '<' not in token.text and '=' not in token.text):
        if(token.pos_=="NOUN" and 24>len(token)>1 and token.text.isnumeric()==False):
            word=token.text.lower()
            dict_keys=words_dict_candidate.keys()
            if word in dict_keys:
                words_dict_candidate[word]=words_dict_candidate[word]+1
            else:
                words_dict_candidate[word]=1
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
        final_result_dict[file.split('.csv')[0].title()]=points
    final_result_dict=sorted(final_result_dict.items(), key=operator.itemgetter(1), reverse=True)
    print((colored(final_result_dict, 'green')))