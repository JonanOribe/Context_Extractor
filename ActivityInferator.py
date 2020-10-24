import os
import pandas as pd
import spacy
from spacy.lang.es.examples import sentences

import requests

import configparser

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

#spacy.load('es')

nlp = spacy.load('es_core_news_sm')
arr_points_values=[12,8,6,2]
ENCODING='utf8'
SEPARATOR=';'

config = configparser.RawConfigParser()
config.read('config_file.ini',encoding=ENCODING)
dictionaries_path=config['DEFAULT']['dictionaries_path']

#Generate dictionaries
articles_path = './articles/'

for r, d, f in os.walk(articles_path):
    for directory in d:
        path2=articles_path+directory
        dictionary_for_keywords=[]
        words_dict={}
        for r2,d2,f2 in os.walk(path2):
            print(path2)
            for file in f2:
                print(file)
                articleFile = open('{}{}{}'.format(path2,'/',file),'r',encoding=ENCODING)
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
            print(words_dict)
            df = pd.DataFrame()
            df['Word']=words_dict.keys()
            df['Count']=words_dict.values()
            df.to_csv('{}{}{}'.format(dictionaries_path,directory,'.csv'),sep=SEPARATOR,encoding=ENCODING,index=False)

#Cleaning data
for r, d, f in os.walk(dictionaries_path):
    for file in f:
        print(dictionaries_path)
        print(file)
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        #print(df)
        quantile=df['Count'].quantile(.8)
        print(quantile)
        df=df[df.Count > quantile]
        print(df)
        df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

#Filter common words between dictionaries
macroDictionary=[]
macroDictionary_dict={}
number_of_dicts=0

for r, d, f in os.walk(dictionaries_path):
    number_of_dicts=len(f)
    for file in f:
        print(dictionaries_path)
        print(file)
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
        print(dictionaries_path)
        print(file)
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)

        for index, row in df.iterrows():
            if row['Word'] in out_of_bounds:
                df.drop([index], inplace=True)

        df.sort_values(by=['Count'], ascending=False,inplace=True)
        df.to_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING,index=False)

#SORTING THE DATA BY COUNTS AND Adding weigths

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        print(dictionaries_path)
        print(file)
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        df['Points']=0
        arr_points=[]
        #print(df['Points'])
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
#r = requests.get('http://www.x-plane.es/')
#r = requests.get('https://www.milanuncios.com/barcos-a-motor-en-vizcaya/')
#r = requests.get('https://www.cosasdebarcos.com/barcos-ocasion/en-vizcaya-49/')
#r = requests.get('https://www.google.com/intl/es_ALL/drive/using-drive/')
r = requests.get('https://www.cosasdebarcos.com/empresas-nauticas-tienda-nautica-6/en-vizcaya-49/')
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
#df.to_csv('../Inferator/dictionaries/'+directory+'.csv',sep=';',encoding='utf8',index=False)

for r, d, f in os.walk(dictionaries_path):
    for file in f:
        print(dictionaries_path)
        print(file)
        count=0
        points=0
        df_words={}
        df=pd.read_csv('{}{}'.format(dictionaries_path,file), sep=SEPARATOR,encoding=ENCODING)
        for index, row in df.iterrows():
            df_words[row['Word']]=row['Points']
        df_words_keys=df_words.keys()
        for index, row in df_from_candidate.iterrows():
            if row['Word'] in df_words_keys:
                #print(row['Word'])
                points=points+df_words[row['Word']]
                count=count+1
        print(file+": "+str(count)+" similarities with "+str(points)+" points")

