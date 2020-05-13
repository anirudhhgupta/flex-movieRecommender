from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import nltk
import json
import numpy as np
import pandas as pd
import logging
import sys
import string
import re

RE_PUNCT = re.compile('([%s])+' % re.escape(string.punctuation), re.UNICODE)

def title(text):

    # Remove all punctuation and make all lowercase 
    return RE_PUNCT.sub(" ", text).lower().split()

class modelRecommendations:
    def preprocess(text):
        
        '''Takes in a string of text, then performs the following:
        1. Remove all punctuation
        2. Remove all stopwords
        3. Return the cleaned text as a list of words
        4. Remove words
        '''
        stemmer = WordNetLemmatizer()
        nopunc = [char for char in text if char not in string.punctuation]
        nopunc = ''.join([i for i in nopunc if not i.isdigit()])
        nopunc =  [word.lower() for word in nopunc.split() if word not in stopwords.words('english')]
       
        return [stemmer.lemmatize(word) for word in text]

    def recommend(movieTitle, titles, model, documents, ids):
        # doctag = title(movieTitle)
        topResults=40
        idss=[None]*topResults
        name=[None]*topResults
        score=[None]*topResults
        final=[]
        # ans=model.docvecs.most_similar('_'.join(doctag),topn=topResults)
        ans=model.docvecs.most_similar([titles[movieTitle]],topn=topResults)
        for i in range(topResults):
            # print(ans[i][0])
            idss[i]=list(ids.keys())[list(ids.values()).index(ans[i][0])]
            name[i]=documents.loc[str(idss[i])]['title']
            score[i]=ans[i][1]
        recommendations=list(zip(name,idss,score))
        return recommendations 
