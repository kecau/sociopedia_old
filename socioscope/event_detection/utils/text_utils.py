import re


def remove_emoji(text):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def remove_url(text): 
    url_pattern = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return url_pattern.sub(r'', text)

def remove_email(text):
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
    return email_pattern.sub(r'', text)

def remove_mention(text):
    mention_pattern = re.compile(r'@+\w+')
    return mention_pattern.sub(r'', text)
    
def remove_number(text):
    number_pattern = re.compile(r'[0-9]+')
    return number_pattern.sub(r'', text)

def remove_hashtag(text):
    hashtag_pattern = re.compile(r'#+\w+')
    return hashtag_pattern.sub(r'', text)

def remove_stopwords(text):
    tokens = text.split()
    pass
    
def pre_process(text):
#     text = s.text
    text = text.replace("\/", '/')
#     text = text.lower()
    
    text = remove_emoji(text)
    text = remove_url(text)
    text = remove_email(text)
    text = remove_mention(text)
    # text = remove_number(text)
    text = remove_hashtag(text)
    
    return ' '.join(text.split())