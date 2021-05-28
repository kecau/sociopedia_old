import re
from django.db import models
from django.utils import timezone
from datetime import date
from django.conf import settings
from django.contrib.auth.models import User
import json
# Create your models here.

class TwitterToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=User.objects.get(pk=1).id, related_name='tokens')
    consumer_key = models.CharField(max_length=100)
    consumer_secret = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)
    access_token_secret = models.CharField(max_length=100)
    used_count = models.IntegerField(default=0)

    def __str__(self):
        return self.consumer_key


class Keyword(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=User.objects.get(pk=1).id, related_name='keywords')
    keyword = models.CharField(max_length=200)
    search_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_streaming = models.BooleanField(default=True)
    error_code = models.IntegerField(default=0)
    is_forced_stop = models.BooleanField(default=False)

    def __str__(self):
        return self.keyword


class Tweet(models.Model):
    keyword = models.ForeignKey('event_detection.Keyword', on_delete=models.CASCADE, related_name='tweets')
    tweet_id = models.BigIntegerField()
    created_at = models.DateTimeField()
    user_id = models.BigIntegerField()
    # user = models.CharField(max_length=50)
    # is_retweet = models.BooleanField(default=False)
    # is_quote = models.BooleanField(default=False)
    retweeted_id = models.BigIntegerField()
    quoted_id = models.BigIntegerField()
    text = models.TextField()
    quoted_text = models.TextField()

    def __str__(self):
        return self.text

    # def toJSON(self):
    #     return json.dumps(self, default=lambda o: o.__dict__, 
    #         sort_keys=True, indent=4)


class Knowledge(models.Model):
    tweet = models.ForeignKey('event_detection.Tweet', on_delete=models.CASCADE, related_name='knowledge')
    k_subject = models.TextField()
    k_predicate = models.TextField()
    k_object = models.TextField()
    subject_type = models.CharField(max_length=100, default='')
    object_type = models.CharField(max_length=100, default='')

    def __str__(self):
        return ", ".join([self.k_subject, self.k_predicate, self.k_object, self.subject_type, self.object_type])
