import os
from django.contrib import messages
import spacy
from neo4j import GraphDatabase
import json


class Neo4jConnection:

    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.__driver is not None:
            self.__driver.close()

    def query(self, query, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query))
            # response = session.run(query)
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response


def filter_spans(spans):
    # Filter a sequence of spans so they don't contain overlaps
    get_sort_key = lambda span: (span.end - span.start, -span.start)
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for span in sorted_spans:
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            result.append(span)
        seen_tokens.update(range(span.start, span.end))
    result = sorted(result, key=lambda span: span.start)
    return result

def query_selector(question):
    query = "Match (s1:Country)<-[r1:BASED_IN]-(b:Bidder)-[r:RELATION]->(t:Target)-[r2:BASED_IN]->(s2:Country) XAYZ XYZ return b,r,t,s1,s2,r1,r2 Limit 30"
    condition = ""
    relation = ""

    nlp2 = spacy.load("./staticfiles/Ques_NLP_model_2.0")
    doc = nlp2(question)
    spans = list(doc.ents)
    spans = filter_spans(spans)
    # retokenizing doc with updated values from filter_span
    with doc.retokenize() as retokenizer:
        for span in spans:
            retokenizer.merge(span)
    for a in filter(lambda w: w.ent_type_ == "BIDDER", doc):
        # print(a)
        a = str(a)
        # a = a.lower()
        if condition != "":
            condition = condition + " and"
        condition = condition + " b.name='" + a + "'"

    for a in filter(lambda w: w.ent_type_ == "TARGET", doc):
        # print(a)
        # a = str(a)
        # a = a.lower()
        if condition != "":
            condition = condition + " and"
        condition = condition + " t.name='" + a + "'"

    for a in filter(lambda w: w.ent_type_ == "BIDDER_GPE", doc):
        # print(a)
        a = str(a)
        a = a.lower()
        if condition != "":
            condition = condition + " and"
        condition = condition + " s1.name='" + a + "'"

    for a in filter(lambda w: w.ent_type_ == "Target_GPE", doc):
        a = str(a)
        a = a.lower()
        if condition != "":
            condition = condition + " and"
        condition = condition + " s2.name='" + a + "'"

    for a in filter(lambda w: w.ent_type_ == "BIDDER_IND", doc):
        a=str(a)
        a=a.lower()
        a=a.replace(" industry","")
        if condition != "":
            condition = condition + " and"
        condition = condition + " b.industry='" + a + "'"

    for a in filter(lambda w: w.ent_type_ == "Target_IND", doc):
        a=str(a)
        a = a.lower()
        a = a.replace(" industry", "")
        if condition != "":
            condition = condition + " and"
        condition = condition + " t.industry='" + a + "'"

    for a in filter(lambda w: w.ent_type_ == "RELATION", doc):
        a = a.lemma_.lower()
        print(a)
        if a == "acquisition" or a == "acquisitions":
            a = "acquire"
        elif a == "merger":
            a = "merge"
        if a == "merge" or a == "acquire":
            relation = relation + " r.type='" + str(a) + "'"

    if (condition == "" and relation != "") or (condition != "" and relation == ""):
        query = query = query.replace('XAYZ', "where XAYZ")
        query = query = query.replace('XYZ', condition)
        query = query = query.replace('XAYZ', relation)
    elif (condition != "" and relation != ""):
        query = query = query.replace('XAYZ', "where XAYZ")
        relation = relation + " and"
        query = query = query.replace('XAYZ', relation)
        query = query = query.replace('XYZ', condition)

    query = query = query.replace('XAYZ', "")
    query = query = query.replace('XYZ', "")
    return query

def NLI(request,nl_query):
    cypher_query = query_selector(nl_query)
    print(cypher_query)
    messages.success(request, "Cypher Query is:" + cypher_query)
    conn = Neo4jConnection(uri="bolt://localhost:7687", user="yogiraj", pwd="12345")
    output = conn.query(cypher_query, db='Neo4j')
    return output


def node(n,gdn):
    tmp, = n.labels
    if n.id not in gdn.nodes_list:
        gdn.nodes_list.append(n.id)
        if tmp=="Country":
            node = {
            "id": n.id,
            "group": tmp,
            "name": n['name']
            }
        else:
            node = {
                "id": n.id,
                "group": tmp,
                "name": n['name'],
                "industry":n['industry'],
                "type":n['type'],
                "url":n['url'],
                "website":n['website']
            }
        gdn.nodes.append(node)
        return gdn
    else:
        return gdn



def relation(r,gdl):
    # tmp, = r.labels
    if r.id not in gdl.links_list:
        gdl.links_list.append(r.id)
        if r.type=="RELATION":
            link = {
                "id": r.id,
                "group": r['type'],
                "source": r.nodes[0].id,
                "target": r.nodes[1].id,
                "news": r['news']
            }
        else:
            link = {
                "id": r.id,
                "group": r.type,
                "source": r.nodes[0].id,
                "target": r.nodes[1].id

            }
        gdl.links.append(link)
        return gdl
    else:
        return gdl

class graph_data_node:
    nodes = []
    nodes_list = []

class graph_data_link:
    links = []
    links_list = []

def save_as_json(a):
    n=graph_data_node()
    n.nodes = []
    n.nodes_list = []
    l=graph_data_link()
    l.links = []
    l.links_list = []
    if a==None:
        return
    for i in a:
        for k in i:
            #print(str(type(k)))
            if str(type(k)) == "<class 'neo4j.graph.Node'>":
                #print(n.nodes_list)
                n=node(k,n)
            else:
                l=relation(k,l)
    data = {
        "nodes": n.nodes,
        "links": l.links,
    }
    json_object = json.dumps(data, indent=4)
    os.remove("./staticfiles/sample.json")
    with open("./staticfiles/sample.json", "w") as outfile:
        outfile.write(json_object)
    return data





def execute(request,nl_query):
    print("none")
    messages.success(request, "Query is:"+nl_query)
    data=NLI(request,nl_query)
    #messages.success(request, data)
    messages.success(request, "Query ran successfully")
    a=save_as_json(data)
    messages.success(request, "Json Saved")
    #messages.success(request, "nodes: "+str(a))
    return a
