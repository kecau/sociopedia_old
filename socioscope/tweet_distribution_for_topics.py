import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

import collections
import string
import re
import nltk
from nltk.util import ngrams

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from SPARQLWrapper import SPARQLWrapper, JSON

nltk.download('punkt')

stopwords = set(STOPWORDS)
stopwords.update(["https", "amp", "rt", "co", "i"])
sparql = SPARQLWrapper("http://dbpedia.org/sparql")

def link_entity(entity, entity_type, limit=100):
    sparql.setQuery(
        """
        SELECT distinct *
        
        WHERE { 
        
        ?entity rdfs:label ?name
        FILTER (contains(?name, "%s"))
        
        }
        
        LIMIT %d
        """ % (entity, limit)
    )

    d = {}
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            d[result["entity"]["value"]] = result["name"]["value"]
    except Exception as e:
        print(e)

    return d

def entity_relate_object(entity):
    sparql.setQuery(
        """
        SELECT distinct *
        
        WHERE { 
                
        <%s> ?predicate ?object

        }
        """ % (entity)
    )

    d = {}
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            object_type = result["object"]["type"]
            object_value = result["object"]["value"]
            lang = None
            if "xml:lang" in result["object"]:
                lang = result["object"]["xml:lang"]

            if lang is None or lang == 'en':
                if object_type != 'uri' and len(object_value) < 100:
                    predicate = result["predicate"]["value"].split('/')[-1]
                    d[predicate] = object_value
    except Exception as e:
        print(e)

    return d


def suggest_topic_from_ngrams(keyword):
    file_path = f'/home/thinh/sociopedia/{keyword}.csv'

    one_gram_counter = collections.Counter()
    two_gram_counter = collections.Counter()
    # thr_gram_counter = collections.Counter()

    with open(file_path) as file:
        for line_num, line in enumerate(file):
            if line_num % 100000 == 0:
                print(line_num)
            line_arr = line.strip().split(',')
            if len(line_arr) == 8:
                time = line_arr[1].strip()
                tweet = line_arr[6].strip()
            
                text = tweet.translate(str.maketrans('', '', string.punctuation + "”’“…|"))
                text = " ".join([word for word in text.split() if not word.lower() in stopwords])
                tokens = nltk.word_tokenize(text)
                
                one_gram = ngrams(tokens, 1)
                one_gram_counter.update(one_gram)
                
                two_gram = ngrams(tokens, 2)
                two_gram_counter.update(two_gram)
                
                # thr_gram = ngrams(tokens, 3)
                # thr_gram_counter.update(thr_gram)

    detect_topics = []
    for key, _ in one_gram_counter.most_common()[:40]:
        word = " ".join(key).lower()
        if word != keyword and word not in detect_topics:
            detect_topics.append(word)
            
    for key, _ in two_gram_counter.most_common()[:20]:
        word = " ".join(key).lower()
        if word != keyword and word not in detect_topics:
            detect_topics.append(word)
            
    # for key, _ in thr_gram_counter.most_common()[:20]:
    #     word = " ".join(key).lower()
    #     if word != keyword and word not in detect_topics:
    #         detect_topics.append(word)

    return detect_topics

def suggest_topic_from_dbpedia(keyword):
    try:
        d = link_entity(keyword, None, limit=1)
        if d is None or len(d) == 0:
            return []

        related_keywords = []

        for entity, name in d.items():
            related_entity_dict = entity_relate_object(entity)

            for predicate, object_value in related_entity_dict.items():
                related_keywords.append(object_value)

            return related_keywords
    except Exception as e:
        return []

def tweet_distribution(keyword):
    file_path = f'/home/thinh/sociopedia/{keyword}.csv'

    ngram_topics = suggest_topic_from_ngrams(keyword)
    print('Ngram topics:', ngram_topics)
    dbpedia_topics = suggest_topic_from_dbpedia(keyword)
    print('Dbpedia topics:', dbpedia_topics)

    detect_topics = [keyword] + ngram_topics + dbpedia_topics
    print('All topics:', detect_topics)

    counter = {}
    with open(file_path) as file:
        for line_num, line in enumerate(file):
            if line_num % 100000 == 0:
                print(line_num)
            line_arr = line.strip().split(',')
            if len(line_arr) == 8:
                time = line_arr[1].strip()
                tweet = line_arr[6].strip().lower()

                text = tweet.translate(str.maketrans('', '', string.punctuation + "”’“…|"))
                text = " ".join([word for word in text.split() if not word.lower() in stopwords])
                
                time_hour = time[:-6]
                if time_hour not in counter:
                    counter[time_hour] = [0] * len(detect_topics)
                
                for i, word in enumerate(detect_topics):
                    if word in text:
                        counter[time_hour][i] += 1

    df = pd.DataFrame.from_dict(counter, orient='index').reset_index()
    df.columns = ['time'] + detect_topics
    df.to_csv(f'/home/thinh/sociopedia/{keyword}_topics.csv')

if __name__ == "__main__":
    keywords = ['trump', 'biden', 'debate', 'america', 'china', 'tiktok', 'covid', 'racist']
    # keywords = ['tiktok']
    for keyword in keywords:
        print('###Running for keyword:', keyword)
        tweet_distribution(keyword)