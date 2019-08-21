#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().system('pip install -U spacy')
get_ipython().system('python -m spacy download en')
get_ipython().system('python -m spacy download es')


# In[93]:


import os
import pandas as pd
from spacy.lang.es.examples import sentences 
nlp = spacy.load('es_core_news_sm')

#Generate dictionaries
path = './articles/'
for r, d, f in os.walk(path):   
    for directory in d:
        path2=path+directory
        dictionary_for_keywords=[]
        for r2,d2,f2 in os.walk(path2):
            print(path2)
            for file in f2:
                print(file)
                articleFile = open(path2+'/'+file,'r',encoding='utf8') 
                article=articleFile.read()

                doc=nlp(article)

                for token in doc:
                    if(token.pos_=="NOUN" and len(token)>1):
                        #print(token.text, token.pos_, token.dep_)
                        dictionary_for_keywords.append(token.text)
            dictionary_for_keywords_with_filter = list(dict.fromkeys(dictionary_for_keywords))
            df = pd.DataFrame(dictionary_for_keywords_with_filter)
            df.to_csv('../Inferator/dictionaries/'+directory+'.csv',sep=';',encoding='utf8')


# 

# In[ ]:


#Filter common words between dictionaries

