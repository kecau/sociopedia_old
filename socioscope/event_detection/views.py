from django.shortcuts import render, redirect
from .forms import KeywordSearchForm, KeywordAnalysisForm, SelectTimeRangeForm, TokenAddForm
from .utils import twitter_search, knowledge_extract
from django.http import JsonResponse
from .models import Keyword, Tweet, TwitterToken
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.serializers.json import DjangoJSONEncoder
from plotly.offline import plot
import plotly.graph_objs as go
import collections
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from wordcloud import WordCloud, STOPWORDS
import threading
from django.core import serializers
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import utils
from event_detection.utils import dbpedia_query, event_detect, knowledge_graph_extract
import base64
import ast


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def search(request):
    if request.method == 'POST':
        form = KeywordSearchForm(request.POST, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            print('end_date', post.end_date)
            
            keyword_obj_list = []
            for keyword in post.keyword.strip().split(','):
                keyword_obj = Keyword.objects.create(user=request.user, keyword=keyword.strip(), search_date=timezone.now(), end_date=post.end_date)
                keyword_obj_list.append(keyword_obj)

            used_token = form.cleaned_data['token_selection']
            stream = twitter_search.stream_search(keyword_obj_list, used_token)
            is_error = None
            if stream is None:
                is_error = True
                
            return render(request, 'keyword_search.html', {'title': 'search', 'form': form, 'keyword_obj_list': keyword_obj_list, 'is_error': is_error})
       
    # else:
    form = KeywordSearchForm(user=request.user)
    end_date = timezone.now() + timedelta(7)
    form['end_date'].initial = end_date
    min_date = timezone.now().strftime("%Y/%m/%d")
    max_date = end_date.strftime("%Y/%m/%d")

    # user_tokens = request.user.tokens.all()
    # admin_user = User.objects.get(username='admin')
    # admin_tokens = admin_user.tokens.all()
    # tokens = user_tokens | admin_tokens


    # form['token_selection'].initial.queryset = tokens
    return render(request, 'keyword_search.html', {'title': 'search', 'form': form, 'min_date': min_date, 'max_date': max_date})

@login_required
def data_analysis(request, pk, start_date, end_date):
    # tweet_list = utils.get_tweet_in_time_range(pk, start_date, end_date)

    return render(request, 'keyword_analysis.html', {"keyword_id": pk, "start_date": start_date, "end_date": end_date})

@csrf_exempt
def analyse(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)
        analyse_type = request.POST.get('analyse_type')
       
        tweet_list = utils.get_tweet_in_time_range(keyword_id, start_date, end_date)

        if analyse_type == 'wordcloud':
            img_path = utils.analyse_wordcloud(tweet_list, request)
            return JsonResponse({'wordcloud': img_path}, status=200)

        elif analyse_type == 'n-grams':
            one_gram_plot_div, two_gram_plot_div, thr_gram_plot_div = utils.analyse_ngrams(tweet_list)
            return JsonResponse({
                'one-grams': one_gram_plot_div, 
                'two-grams': two_gram_plot_div, 
                'thr-grams': thr_gram_plot_div, 
                },
                status=200)

        elif analyse_type == 'knowledgegraph':
            knowledge_graph_dict = utils.extract_knowledge_graph(tweet_list)
            return JsonResponse({'knowledgegraph': knowledge_graph_dict}, status=200)
        
    return JsonResponse({"error": ""}, status=400)


def detect_event(request, pk, start_date, end_date):
    return render(request, 'event_detection.html', {"keyword_id": pk, "start_date": start_date, "end_date": end_date})

@csrf_exempt
def load_keyword_ajax(request):
    if request.is_ajax and request.method == "POST":
        keywords = []

        keyword_id = request.POST.get('id', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)

        tweet_list = utils.get_tweet_in_time_range(keyword_id, start_date, end_date)
        one_gram_counter, two_gram_counter, thr_gram_counter = utils.extract_ngrams(tweet_list)
         
        keywords.extend([' '.join(value[0]) for value in one_gram_counter.most_common()[:20]])
        keywords.extend([' '.join(value[0]) for value in two_gram_counter.most_common()[:20]])
        keywords.extend([' '.join(value[0]) for value in thr_gram_counter.most_common()[:20]])

        dbpedia_keywords = utils.suggest_keyword_from_dbpedia(keyword_id)
        # keywords.extend(dbpedia_keywords)
        
        return JsonResponse({'keywords': keywords, 'dbpedia_keywords': dbpedia_keywords}, status=200)

    return JsonResponse({"error": ""}, status=400)

@csrf_exempt
def detect_event_ajax(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)
        keyword = request.POST.get('filter_key', None)

        # tweet_list = utils.get_tweet_with_filter_key(pk, filter_key)
        tweet_list = utils.get_tweet_in_time_range(keyword_id, start_date, end_date)
        time_option = 'hour'
        x_data_date, y_data_event, y_data, y_proportion = event_detect.get_tweet_distribution_event(tweet_list, keyword, time_option)
        plot_div = utils.plot_distribution_event(x_data_date, y_data_event, y_proportion)

        burst_list, variables = event_detect.detect_event(y_data_event, y_data)
        event_plot_div = utils.plot_burst_timeline(x_data_date, burst_list, variables)

        events = []
        bursts = burst_list[0]
        for index, burst in bursts.iterrows():
            start = burst['begin']
            end = burst['end']
            
            start_time = x_data_date[start] #.strftime("%Y-%m-%d %H:%M")
            end_time = x_data_date[end] #.strftime("%Y-%m-%d %H:%M")
            
            events.append((start_time, end_time))

        return JsonResponse({'plot_div': plot_div, 'event_plot_div': event_plot_div, 'events': events}, status=200)

    return JsonResponse({"error": ""}, status=400)

def event_knowledge(request, pk, start_date, end_date):
    return render(request, 'event_knowledge.html', {"keyword_id": pk, "start_date": start_date, "end_date": end_date})

@csrf_exempt
def event_knowledge_ajax(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)

        tweet_list = utils.get_tweet_in_time_range(keyword_id, start_date, end_date)
        knowledge_graph_dict = utils.extract_knowledge_graph(tweet_list)

        return JsonResponse({'knowledgegraph': knowledge_graph_dict}, status=200)

    return JsonResponse({"error": ""}, status=400)

def knowledge_graph_linking(request, entity, knowledge_graph):
    base64_bytes = knowledge_graph.encode('utf-8')
    message_bytes = base64.b64decode(base64_bytes)
    keyword_extracted_graph = message_bytes.decode('utf-8')
    keyword_extracted_graph = ast.literal_eval(keyword_extracted_graph)

    keyword_dbpedia_graph = utils.get_keyword_dbpedia_graph(entity)
    
    keyword_knowledge_graph = []
    for key, value in keyword_extracted_graph.items():
        rel = "_".join(key.split("_")[:-1])
        rel_type = key.split("_")[-1]
        if 'tail' == rel_type:
            keyword_knowledge_graph.append([entity, rel, value, 'extracted'])
        elif 'head' == rel_type:
            keyword_knowledge_graph.append([value, rel, entity, 'extracted'])

    keyword_knowledge_graph.append([entity, 'same as', "dbo:" + entity, 'dbpedia'])
    
    if keyword_dbpedia_graph is not None:
        # keyword_knowledge_graph.extend(keyword_dbpedia_graph)
        for key, value in keyword_dbpedia_graph.items():
            keyword_knowledge_graph.append(["dbo:" + entity, key, value, 'dbpedia'])

    return render(request, 'knowledge_graph_linking.html', {"entity": entity, "knowledge_graph": keyword_knowledge_graph, "dbpedia_graph": keyword_dbpedia_graph})

@login_required
def system_management(request):
    keywords = request.user.keywords.all()
    current_time = timezone.now()
    for keyword in keywords:
        if keyword.end_date < current_time:
            keyword.is_streaming = False
        # else:
        #     keyword.is_streaming = True
            
        keyword.n_tweets = keyword.tweets.count()

    return render(request, 'system_management.html', {'title': 'system_management', 'keywords': keywords})

def api_document(request):
    return render(request, 'api_document.html', {'title': 'api_document'})

@csrf_exempt
def delete_keyword(request):
    if request.method == "GET":
        keyword_id = request.GET.get('keyword_id', None)
        Keyword.objects.filter(id=keyword_id).delete()
        
        return JsonResponse({"id": keyword_id}, status=200)

    return JsonResponse({"error": "not ajax request"}, status=400)

@csrf_exempt
def stop_streaming(request):
    if request.method == "GET":
        keyword_id = request.GET.get('keyword_id', None)
        Keyword.objects.filter(id=keyword_id).update(is_forced_stop=True)
        
        return JsonResponse({"id": keyword_id}, status=200)

    return JsonResponse({"error": "not ajax request"}, status=400)

@login_required
def view_tweets(request, pk):
    tweet_list = Tweet.objects.filter(keyword=pk)
    # plot_div = utils.plot_distribution(tweet_list)

    page = request.GET.get('page', 1)
    tweets, tweet_index, page_range = utils.paging_tweets(tweet_list, page)
    
    form = SelectTimeRangeForm()

    page_settings = {}
    page_settings['has_other_pages'] = tweets.has_other_pages()
    page_settings['has_previous'] = tweets.has_previous()
    page_settings['number'] = tweets.number
    page_settings['has_next'] = tweets.has_next()
    if tweets.has_previous():
        page_settings['previous_page_number'] = tweets.previous_page_number()
    if tweets.has_next():
        page_settings['next_page_number'] = tweets.next_page_number()

    return render(request, 'view_tweets.html', {'title': 'system_management',
                                                'keyword_id': pk,
                                                'tweets': tweets.object_list, 
                                                'page_settings': page_settings,
                                                'tweet_index': tweet_index, 
                                                'page_range': page_range,
                                                # 'plot_div': plot_div,
                                                'form': form})

@csrf_exempt
def load_tweet_dist(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)
        time_option = request.POST.get('time_option', 'minute')

        tweet_list = Tweet.objects.filter(keyword=keyword_id)
        plot_div = utils.plot_distribution(tweet_list, time_option=time_option)
        return JsonResponse({'plot_div': plot_div}, status=200)

    return JsonResponse({"error": ""}, status=400)

@csrf_exempt
def filter_tweets_intime(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)
        page_n = request.POST.get('page_n', None)
        tweet_list = utils.get_tweet_in_time_range(keyword_id, start_date, end_date)

        page = int(page_n)
        tweets, tweet_index, page_range = utils.paging_tweets(tweet_list, page)

        page_settings = {}
        page_settings['has_other_pages'] = tweets.has_other_pages()
        page_settings['has_previous'] = tweets.has_previous()
        page_settings['number'] = tweets.number
        page_settings['has_next'] = tweets.has_next()
        if tweets.has_previous():
            page_settings['previous_page_number'] = tweets.previous_page_number()
        if tweets.has_next():
            page_settings['next_page_number'] = tweets.next_page_number()

        # for tweet in tweets:
        #     tweet.user_id = str(tweet.user_id)
        #     tweet.tweet_id = str(tweet.tweet_id)
            
        tweets = serializers.serialize('json', tweets)
        
        return JsonResponse({"tweets": tweets, "tweet_index": tweet_index, "page_range": page_range, 'page_settings': page_settings}, status=200)

    return JsonResponse({"error": ""}, status=400)

@csrf_exempt
def link_entity_dbpedia(request):
    if request.is_ajax and request.method == "POST":
        entity = request.POST.get('entity', None)
        entity_type = request.POST.get('type', None)
        
        dbpedia_entity = dbpedia_query.link_entity(entity, entity_type)

        return JsonResponse({'dbpedia_entity': dbpedia_entity}, status=200)

    return JsonResponse({"error": ""}, status=400)

@csrf_exempt
def question_answering_ajax(request):
    if request.is_ajax and request.method == "POST":
        question = request.POST.get('question', None)
        entities, relations = knowledge_graph_extract.extract_entity_question(question)

        return JsonResponse({'entities': entities, 'relations': relations}, status=200)

    return JsonResponse({"error": ""}, status=400)

def token_management(request):
    if request.method == 'POST':
        form = TokenAddForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
    
    form = TokenAddForm()
    
    user_tokens = request.user.tokens.all()
    admin_user = User.objects.get(username='admin')
    admin_tokens = admin_user.tokens.all()

    # for token in list(admin_tokens):
    #     token.consumer_key = token.consumer_key[:3] + "".join(["*" for i in range(len(token.consumer_key) - 3)]) 
    #     token.consumer_secret = token.consumer_secret[:3] + "".join(["*" for i in range(len(token.consumer_secret) - 3)]) 
    #     token.access_token = token.access_token[:3] + "".join(["*" for i in range(len(token.access_token) - 3)]) 
    #     token.access_token_secret = token.access_token_secret[:3] + "".join(["*" for i in range(len(token.access_token_secret) - 3)]) 

    tokens = user_tokens #| admin_tokens
    # tokens = list(user_tokens)
    # tokens.extend(list(admin_tokens))

    return render(request, 'token_management.html', {'title': 'token_management', 'form': form, 'tokens': tokens})

def delete_token(request, pk):
    if request.method == 'POST':
        form = TokenAddForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()

    form = TokenAddForm()
    
    user_tokens = request.user.tokens.all()
    admin_user = User.objects.get(username='admin')

    delete_token = TwitterToken.objects.filter(id=pk).first()
    if request.user != admin_user and delete_token.user == admin_user:
        pass
    else:
        delete_token.delete()    

    admin_tokens = admin_user.tokens.all()

    # for token in list(admin_tokens):
    #     token.consumer_key = token.consumer_key[:3] + "".join(["*" for i in range(len(token.consumer_key) - 3)]) 
    #     token.consumer_secret = token.consumer_secret[:3] + "".join(["*" for i in range(len(token.consumer_secret) - 3)]) 
    #     token.access_token = token.access_token[:3] + "".join(["*" for i in range(len(token.access_token) - 3)]) 
    #     token.access_token_secret = token.access_token_secret[:3] + "".join(["*" for i in range(len(token.access_token_secret) - 3)]) 

    tokens = user_tokens #| admin_tokens
    # tokens = list(user_tokens)
    # tokens.extend(list(admin_tokens))

    return render(request, 'token_management.html', {'title': 'token_management', 'form': form, 'tokens': tokens})

@csrf_exempt
def token_streaming_count_check(request):
    if request.is_ajax and request.method == "POST":
        token_id = request.POST.get('token_id', None)
        token = TwitterToken.objects.filter(id=token_id).first()
        streaming_count = token.used_count

        return JsonResponse({'streaming_count': streaming_count}, status=200)

    return JsonResponse({"error": ""}, status=400)

def home(request):
    return render(request, 'home.html', {'title': 'home'})

def about(request):
    return render(request, 'about.html', {'title': 'about'})
