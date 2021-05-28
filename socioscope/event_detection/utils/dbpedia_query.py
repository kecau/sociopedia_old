from SPARQLWrapper import SPARQLWrapper, JSON

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

def entity_relate_object_two_level(entity):
    print(entity)
    sparql.setQuery(
        """
        SELECT distinct *
        
        WHERE { 
                
        <%s> ?predicate ?object .
        OPTIONAL {
            ?object ?sub_predicate ?sub_object
        }
                
        }
        """ % (entity)
    )

    triples = set()
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
                    triples.add((entity + "_DBpedia", predicate, object_value, 'dbpedia'))

                    sub_object_type = result["sub_object"]["type"]
                    sub_object_value = result["sub_object"]["value"]

                    if sub_object_type != 'uri' and len(sub_object_value) < 100:
                        sub_predicate = result["sub_predicate"]["value"].split('/')[-1]
                        triples.add((object_value, sub_predicate, sub_object_value, 'dbpedia'))


    except Exception as e:
        print(e)

    print('dbpedia:', len(triples))
    return triples
