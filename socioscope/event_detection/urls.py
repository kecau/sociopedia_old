from django.urls import path, include
from . import views, views_api
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token


# router = routers.DefaultRouter()
# router.register(r'keywords', views.KeywordViewSet)

urlpatterns = [
    path('signup', views.signup, name='signup'),

    path('search', views.search, name='search'),
    path('system_management', views.system_management, name='system_management'),
    path('api_document', views.api_document, name='api_document'),
    path('token_management', views.token_management, name='token_management'),
    
    # path('word_cloud', views.word_cloud, name='word_cloud'),
    # path('knowledge_graph', views.knowledge_graph, name='knowledge_graph'),
    path('view_tweets/<int:pk>/', views.view_tweets, name='view_tweets'),
    path('data_analysis/<int:pk>/<str:start_date>/<str:end_date>/', views.data_analysis, name='data_analysis'),
    path('detect_event/<int:pk>/<str:start_date>/<str:end_date>/', views.detect_event, name='detect_event'),
    path('event_knowledge/<int:pk>/<str:start_date>/<str:end_date>/', views.event_knowledge, name='event_knowledge'),
    path('knowledge_graph_linking/<str:entity>/<str:knowledge_graph>/', views.knowledge_graph_linking, name='knowledge_graph_linking'),
    path('delete_token/<int:pk>/', views.delete_token, name="delete_token"),

    path('ajax/keyword_search', views.load_tweet_dist, name='load_tweet_dist'),
    path('ajax/keyword', views.delete_keyword, name='delete_keyword'),
    path('ajax/stop_streaming', views.stop_streaming, name='stop_streaming'),
    path('ajax/filter_tweets_intime', views.filter_tweets_intime, name='filter_tweets_intime'),
    path('ajax/analyse', views.analyse, name='analyse'),
    path('ajax/link_entity_dbpedia', views.link_entity_dbpedia, name='link_entity_dbpedia'),
    path('ajax/detect_event_ajax', views.detect_event_ajax, name='detect_event_ajax'),
    path('ajax/event_knowledge_ajax', views.event_knowledge_ajax, name='event_knowledge_ajax'),
    path('ajax/load_keyword_ajax', views.load_keyword_ajax, name='load_keyword_ajax'),
    path('ajax/question_answering_ajax', views.question_answering_ajax, name='question_answering_ajax'),
    path('ajax/token_streaming_count_check', views.token_streaming_count_check, name='token_streaming_count_check'),

    path('', views.home, name='home'),
    # path('home', views.home, name='home'),
    path('about', views.about, name='about'),

    ### API
    # path('sociopedia/', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('keywords/', views_api.KeywordList.as_view(), name='keyword_list'),
    path('tweet_list/', views_api.TweetList.as_view(), name='tweet_list'),
    path('topic_list/', views_api.TopicList.as_view(), name='topic_list'),
    path('event_list/', views_api.EventList.as_view(), name='event_list'),
    path('event_knowledge_list/', views_api.EventKnowledgeList.as_view(), name='event_knowledge_list'),
    path('linking_knowledge/', views_api.LinkingKnowledge.as_view(), name='linking_knowledge'),
]