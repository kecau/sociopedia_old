import pandas as pd
import numpy as np
# import burst_detection as bd
from event_detection.utils import burst_detection as bd
from event_detection.utils import datetime_utils

import collections
from datetime import datetime, timedelta

def get_tweet_distribution(tweet_list, time_option="minute", keyword=None):
    # first_tweet = tweet_list.first()
    # first_time = first_tweet.created_at.timestamp()
    # last_tweet = tweet_list.last()
    # last_time = last_tweet.created_at.timestamp()
    
    # denominator = 60
    # if time_option == 'minute': # minute
    #     denominator = 60
    # elif time_option == 'hour': # hour
    #     denominator = 60 * 60
    # elif time_option == 'day': # day
    #     denominator = 60 * 60 * 24
    # elif time_option == 'week': # week
    #     denominator = 60 * 60 * 24 * 7
    # elif time_option == 'month': # month
    #     denominator = 60 * 60 * 24 * 30
        
    # time_range = int((last_time - first_time) / denominator)
    # if time_range < 1: 
    #     time_range = 1
    # x_data = [i for i in range(time_range)]

    # counter = collections.Counter()
    # for tweet in tweet_list.iterator():
    #     if keyword is None or keyword.lower() in tweet.text.lower(): 
    #         date_time = tweet.created_at.timestamp()
    #         counter.update([int((date_time - first_time) / denominator)])
    
    # y_data = []
    # x_data_date = []
    # for x in x_data:
    #     date = datetime.fromtimestamp(x * denominator + first_time)
    #     x_data_date.append(date)
    #     if x in counter:
    #         y_data.append(counter[x])
    #     else:
    #         y_data.append(0)

    pivot = 0
    if time_option == 'minute': # minute
        pivot = 3
    elif time_option == 'hour': # hour
        pivot = 6
    elif time_option == 'day': # day
        pivot = 9
    elif time_option == 'month': # month
        pivot = 12

    counter = collections.Counter()
    for tweet in tweet_list.iterator():
        if keyword is None or keyword.lower() in tweet.text.lower(): 
            time = tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
            time_short = datetime_utils.correct_time(time[:-pivot])
            counter.update([time_short])

    counter_list = sorted(counter.items())
    x_data_date = [x for x, y in counter_list]
    y_data = [y for x, y in counter_list]

    return x_data_date, y_data

def get_tweet_distribution_event(tweet_list, keyword, time_option="minute"):
    x_data_date, y_data = get_tweet_distribution(tweet_list, time_option)
    x_data_date_event, y_data_event = get_tweet_distribution(tweet_list, time_option, keyword)
    
    y_proportion = []
    for y_event, y in zip(y_data_event, y_data):
        y_proportion.append(y_event/y if y != 0 else 0)

    return x_data_date_event, y_data_event, y_data, y_proportion

def detect_event(r, d):

    r = pd.Series(np.array(r, dtype=float))
    d = pd.Series(np.array(d, dtype=float))

    r = r.mask(r==0).fillna(1)
    d = d.mask(d==0).fillna(1)
    n = len(r)

    # for test
    # d = pd.Series(np.floor(np.ones(n)*1500 + np.random.normal(scale=40, size=n)))
    # r = pd.Series(np.floor(np.ones(n)*100 + np.random.normal(scale=10, size=n)))
    # r[r<0] = 0
    # r[1:3] = r[1:3] + 200 #r[4:8] = r[4:8] + 200

    
    variables = [[1.5, 1.0],
             [2.0, 1.0],
             [3.0, 1.0],
             [4.0, 1.0],
             [2.0, 0.5],
             [2.0, 1.0],
             [2.0, 2.0],
             [2.0, 3.0]]

    burst_list = []
    for v in variables:
        q, _, _, p = bd.burst_detection(r, d, n, v[0], v[1], smooth_win=1)

        label = 's='+str(v[0])+', g='+str(v[1])

        bursts = bd.enumerate_bursts(q, label)
        bursts = bd.burst_weights(bursts, r, d, p)

        burst_list.append(bursts)

    return burst_list, variables
    