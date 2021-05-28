import sys
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "socioscope.settings")
django.setup()
sys.path.append('/data/django/socioscope/event_detection')
import pandas as pd
from event_detection.models import Tweet, Keyword, Knowledge
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware
from event_detection.utils import knowledge_graph_extract, text_utils


def import_tweets(input_file):
    df = pd.read_csv(input_file)

    for i, row in df.iterrows():
        date = parse_datetime(row['date'])
        if not is_aware(date):
            date = make_aware(date) 

        tweet = Tweet(tweet_id=row['tweet_id'],
                created_at=date,
                user_id=row['user_id'],
                user=row['user'],
                is_retweet=bool(row['is_retweet']),
                is_quote=bool(row['is_quote']),
                text=row['text'],
                quoted_text=row['quoted_text'])

        tweet.save()

def import_tweets_of_keyword(keyword_str, input_file):
    keyword_obj = Keyword.objects.filter(keyword=keyword_str)[0]
    print(keyword_obj)
    with open(input_file) as file:
        for line in file:
            line_arr = line.split(',')
            if len(line_arr) == 8:
                tweet_obj = Tweet.objects.create(keyword=keyword_obj,
                                                tweet_id=int(line_arr[0]),
                                                created_at=make_aware(parse_datetime(line_arr[1])), 
                                                user_id=int(line_arr[2]), 
                                                retweeted_id=int(line[4]), 
                                                quoted_id=int(line[5]), 
                                                text=line_arr[6], 
                                                quoted_text=line_arr[7])

                triple_list = knowledge_graph_extract.extract_entity(text_utils.pre_process(line_arr[6]))
                for triple in triple_list:
                    Knowledge.objects.create(tweet=tweet_obj,
                                            k_subject=triple[0],
                                            k_predicate=triple[1],
                                            k_object=triple[2], 
                                            subject_type=triple[3],
                                            object_type=triple[4])
                                            
if __name__ == "__main__":
    # import_tweets('/data_hdd/socioscope/data/tweets.csv.v1')
    import_tweets_of_keyword("Covid", "/data_hdd/socioscope/data/covid_test_import.csv")


# tweet_list = [] 
# with open('/data_hdd/socioscope/data/tweets.csv', 'r') as file:  
#     for i, line in enumerate(file):  
#         if i > 0 and 'donald trump' in line.lower():  
#             try: 
#                 if i % 100 == 0: 
#                     Tweet.objects.bulk_create(tweet_list) 
#                     tweet_list = [] 
#                 row = line.split(',')  
#                 if len(row) != 8: 
#                     continue 
#                 date = parse_datetime(row[1])  
#                 if not is_aware(date):  
#                     date = make_aware(date)   
                
#                 tweet = Tweet(keyword=trump_key,  
#                     tweet_id=row[0],  
#                     created_at=date,  
#                     user_id=row[2],  
#                     user=row[3],  
#                     is_retweet=bool(row[4]),  
#                     is_quote=bool(row[5]),  
#                     text=row[6],  
#                     quoted_text=row[7]) 
                    
#                 tweet_list.append(tweet)  
#             except Exception as e: 
#                 print(f'line: {i} - ', e) 
