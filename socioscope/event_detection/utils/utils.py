import collections
from datetime import datetime, timedelta

from plotly.offline import plot
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px

from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from event_detection.models import Keyword, Tweet
from event_detection.utils import text_utils, knowledge_graph_extract, event_detect, dbpedia_query
from wordcloud import WordCloud, STOPWORDS

import collections
import string
import re
import nltk
from nltk.util import ngrams
nltk.download('punkt')

def plot_distribution(tweet_list, time_option="minute"):
    x_data_date, y_data = event_detect.get_tweet_distribution(tweet_list, time_option)

    fig = go.Figure()
    if len(y_data) < 2:
        bar = go.Bar(x=x_data_date, y=y_data)
    else:
        bar = go.Scatter(x=x_data_date, y=y_data, mode='lines+markers')
    fig.add_trace(bar)
    fig.update_layout(
        xaxis=dict(
            title='Time',
            type='date'
        ),
        yaxis=dict(
            title='Number of tweets'
        ),
        title='Tweets Distribution'
    )

    plot_div = plot(fig,
                    output_type='div', 
                    include_plotlyjs=False,
                    show_link=False, 
                    link_text="")

    return plot_div

def plot_distribution_event(x_data_date, y_data_event, y_proportion):    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    bar_1 = go.Scatter(x=x_data_date, y=y_proportion, mode='lines', name="tweet proportion")
    bar_2 = go.Scatter(x=x_data_date, y=y_data_event, mode='lines', name="number of tweets")
    fig.add_trace(bar_1, secondary_y=False)
    fig.add_trace(bar_2, secondary_y=True)

    fig.update_layout(
        xaxis=dict(
            title='Time',
            type='date'
        ),
        title='Tweets Distribution'
    )

    fig.update_yaxes(title_text="Tweet proportion", secondary_y=False)
    fig.update_yaxes(title_text="Number of tweets", secondary_y=True)

    plot_div = plot(fig,
                    output_type='div', 
                    include_plotlyjs=False,
                    show_link=False, 
                    link_text="")

    return plot_div

def plot_burst_timeline(x_data_date, burst_list, variables):
    fig = go.Figure()

    for i, bursts in enumerate(burst_list):
        label = 's='+str(variables[i][0])+', g='+str(variables[i][1])
        fig.add_trace(go.Scatter(x=x_data_date, y=[i] * len(x_data_date), mode='markers', marker=dict(size=5, color=1), name=label))
        for index, burst in bursts.iterrows():
            start = burst['begin']
            end = burst['end']

            fig.add_trace(go.Scatter(x=[x_data_date[start],x_data_date[start],x_data_date[end],x_data_date[end],x_data_date[start]], 
                                    y=[i-0.2,i+0.2,i+0.2,i-0.2,i-0.2], 
                                    fill="toself",
                                    marker=dict(size=5, color=4),
                                    marker_color='rgba(0, 0, 0, .8)',
                                    showlegend=False))

    plot_div = plot(fig,
                    output_type='div', 
                    include_plotlyjs=False,
                    show_link=False, 
                    link_text="")

    return plot_div


def paging_tweets(tweet_list, page):
    tweet_per_page = 50
    tweet_index = [i + 1 for i in range((int(page) - 1) * tweet_per_page, int(page) * tweet_per_page)]
    paginator = Paginator(tweet_list, tweet_per_page)
    try:
        tweets = paginator.page(page)
    except PageNotAnInteger:
        tweets = paginator.page(1)
    except EmptyPage:
        tweets = paginator.page(paginator.num_pages)

    page_start = tweets.number - 2
    page_end = tweets.number + 3
    if page_start <= 0: page_start = 1
    if page_end > tweets.paginator.page_range[-1] + 1: page_end = tweets.paginator.page_range[-1] + 1

    page_range = list(range(page_start, page_end))
    if page_start > 2:
        page_range = [1, -1] + page_range
    elif page_start > 1:
        page_range = [1] + page_range
    if page_end < tweets.paginator.page_range[-1]:
        page_range = page_range + [-1, tweets.paginator.page_range[-1]]
    elif page_end < tweets.paginator.page_range[-1] + 1:
        page_range = page_range + [tweets.paginator.page_range[-1]]

    for tweet in tweets:
        tweet.user_id = str(tweet.user_id)
        tweet.tweet_id = str(tweet.tweet_id)
        tweet.created_at_str = tweet.created_at.strftime("%Y/%m/%d, %H:%M:%S")

    return tweets, tweet_index, page_range

def get_tweet_in_time_range(pk, start_date, end_date):
    if start_date is None or start_date == "" or start_date == "None":
        start_date = datetime.strptime("1970-01-01 00:00", "%Y-%m-%d %H:%M")
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")

    if end_date is None or end_date == "" or end_date == "None":
        end_date = timezone.now()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M")

    tweet_list = Tweet.objects.filter(keyword=pk, created_at__range=[start_date, end_date]) #.values("text", "created_at")
    return tweet_list

def get_tweet_with_filter_key(pk, filter_key):
    tweet_list = Tweet.objects.filter(keyword=pk, text__icontains=filter_key)
    return tweet_list

def get_keyword_by_id(pk):
    keyword = Keyword.objects.get(pk=pk)
    return keyword

def analyse_wordcloud(tweet_list, request):
    text = " ".join([tweet.text for tweet in tweet_list])
    stopwords = set(STOPWORDS)
    stopwords.update(["https", "amp", "RT", "co", "I"])

    wordcloud = WordCloud(font_path='NanumMyeongjo.ttf', stopwords=stopwords, background_color="white", width=1200, height=700, collocations=False).generate(text)
    wordcloud.to_file(f"event_detection/static/event_detection/{request.user.username}.png")

    return f'event_detection/{request.user.username}.png'

def ngrams_visualization(counter, ngrams):
    count_list = counter.most_common()[:20]
    # count_list.reverse()

    fig = go.Figure()
    bar = go.Bar(x=[' '.join(value[0]) for value in count_list], y=[value[1] for value in count_list])
    fig.add_trace(bar)
    fig.update_layout(
        xaxis=dict(
            title=f'{ngrams}-grams',
        ),
        yaxis=dict(
            title='Count'
        ),
        title=f'{ngrams}-grams Distribution'
    )

    plot_div = plot(fig,
                    output_type='div', 
                    include_plotlyjs=False,
                    show_link=False, 
                    link_text="")

    return plot_div

def extract_ngrams(tweet_list):
    stopwords = set(STOPWORDS)
    stopwords.update(["https", "amp", "rt", "co", "i"])

    tokens = []
    for tweet in tweet_list:
        text = tweet.text.translate(str.maketrans('', '', string.punctuation + "”’“…|"))
        # text = re.sub('[^a-zA-Z0-9]+', ' ', tweet.text) 
        text = " ".join([word for word in text.split() if not word.lower() in stopwords])
        tokens.extend(nltk.word_tokenize(text))

    # tokens = nltk.word_tokenize(' '.join(text_list))
    one_gram = ngrams(tokens, 1)
    two_gram = ngrams(tokens, 2)
    thr_gram = ngrams(tokens, 3)
    one_gram_counter = collections.Counter(one_gram)
    two_gram_counter = collections.Counter(two_gram)
    thr_gram_counter = collections.Counter(thr_gram)

    return one_gram_counter, two_gram_counter, thr_gram_counter

def analyse_ngrams(tweet_list):
    one_gram_counter, two_gram_counter, thr_gram_counter = extract_ngrams(tweet_list)

    one_gram_plot_div = ngrams_visualization(one_gram_counter, 1)
    two_gram_plot_div = ngrams_visualization(two_gram_counter, 2)
    thr_gram_plot_div = ngrams_visualization(thr_gram_counter, 3)

    return one_gram_plot_div, two_gram_plot_div, thr_gram_plot_div

def extract_and_save_knowledge_graph_all_tweets(tweet_list):
    pass

def extract_knowledge_graph(tweet_list):
    exist_ids = set()
    new_tweet_list = []
    for tweet in tweet_list:
        tweet_id = tweet.tweet_id
        retweeted_id = tweet.retweeted_id

        if retweeted_id == 0 or retweeted_id == 1: #0 means not retweet, 1 means retweet
            if tweet_id not in exist_ids:
                exist_ids.add(tweet_id)
                new_tweet_list.append(tweet)
        elif retweeted_id not in exist_ids:
            exist_ids.add(retweeted_id)
            new_tweet_list.append(tweet)
        
    knowledge_graph_dict = {}
    c = 0
    
    for tweet in new_tweet_list:
        knowledge_list = tweet.knowledge.all()
        if knowledge_list is not None and len(knowledge_list) > 0:
            c += 1
            if c > 200: break
            triple_list = []
            for knowledge in knowledge_list:
                triple_list.append((knowledge.k_subject, 
                                    knowledge.k_predicate, 
                                    knowledge.k_object, 
                                    knowledge.subject_type, 
                                    knowledge.object_type))
            
            knowledge_graph_dict[tweet.tweet_id] = (tweet.text, triple_list, tweet.created_at.strftime("%Y/%m/%d, %H:%M:%S"))

    # knowledge_graph_dict = knowledge_graph_extract.extract_triples(tweet_list)

    return knowledge_graph_dict

def suggest_keyword_from_dbpedia(pk):
    keyword = get_keyword_by_id(pk)
    d = dbpedia_query.link_entity(keyword.keyword, None, limit=1)
    related_keywords = []

    for entity, name in d.items():
        related_entity_dict = dbpedia_query.entity_relate_object(entity)

        for predicate, object_value in related_entity_dict.items():
            related_keywords.append(object_value)

        return related_keywords    

def get_keyword_dbpedia_graph(entity):
    d = dbpedia_query.link_entity(entity, None, limit=1)
    
    for entity, name in d.items():
        # related_entity_graph = dbpedia_query.entity_relate_object_two_level(entity)
        related_entity_graph = dbpedia_query.entity_relate_object(entity)

        return related_entity_graph 

