import spacy
nlp = spacy.load("en_core_web_sm") #en_core_web_sm
from event_detection.utils import text_utils

def extract_entity_relation_sent(text):
    doc = nlp(text.strip())
    
    head_entity = ''
    tail_entity = ''
    relation = ''
    
    name_entities = set([ent for ent in doc.ents])
    
    for tok in doc:
        for ent in name_entities:
            if tok.text in str(ent):
                if 'ubj' in tok.dep_:
                    head_entity = str(ent)
                    head_type = ent.label_
                if 'obj' in tok.dep_:
                    tail_entity = str(ent)
                    tail_type = ent.label_
                
        if tok.dep_ == 'ROOT' and tok.pos_ == 'VERB':
            relation = str(tok.text)
    
    if head_entity != '' and tail_entity != '' and relation != '':
        return (head_entity, relation, tail_entity, head_type, tail_type)
    else:
        return None

def extract_entity_relation_sent_ko(text):
    from konlpy.tag import Kkma
    kkma = Kkma()
    try:
        postags = kkma.pos(text)
    except Exception as e:
        print(e)
        return None

    head_entity = ''
    tail_entity = ''
    relation = ''
    head_type = 'KO' #temporary to represent korean entity
    tail_type = 'KO'

    for tag in postags:
        if tag[1][0] == 'N' and head_entity == '':
            head_entity = tag[0]
        elif tag[1][0] == 'V' and relation == '':
            relation = tag[0]
        elif tag[1][0] == 'N' and tail_entity == '' and relation != '':
            tail_entity = tag[0]

    if head_entity != '' and tail_entity != '' and relation != '':
        return (head_entity, relation, tail_entity, head_type, tail_type)
    else:
        return None

def extract_entity(text, lang='en'):
    sents = text.split('.')
    triple_list = []
    for sent in sents:
        if lang == 'en':
            triple = extract_entity_relation_sent(sent)
        elif lang == 'ko':
            triple = extract_entity_relation_sent_ko(sent)

        if triple != None:
            triple_list.append(triple)
            
    return triple_list

def extract_entity_question(question):
    doc = nlp(question.strip().strip('?'))

    entities = []
    relations = []
    for tok in doc:
        if 'ubj' in tok.dep_ or 'obj' in tok.dep_:
            entity = tok.text
            entities.append(entity)
                
        if tok.dep_ == 'ROOT' or tok.pos_ == 'VERB':
            relation = str(tok.text)
            relations.append(relation)
    
    return entities, relations

def extract_triples(tweet_list):
    knowledge_graph_dict = {}
    for tweet in tweet_list:
        text = text_utils.pre_process(tweet.text)
        triple_list = extract_entity(text)
        if len(triple_list) > 0:
            knowledge_graph_dict[tweet.tweet_id] = (tweet.text, triple_list, tweet.created_at.strftime("%Y/%m/%d, %H:%M:%S"))

    return knowledge_graph_dict