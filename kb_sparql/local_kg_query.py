# -*- coding: utf-8 -*-

""" SPARQL queries used for the knowledge graph created in the demonstrator """

QUERY_EVENT = """
PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT DISTINCT ?event ?l ?tbegin ?tend
WHERE {
    ?event rdf:type sem:Event .
    ?event rdfs:label ?l .
    ?event sem:hasBeginTimeStamp ?tbegin .
    ?event sem:hasEndTimeStamp ?tend .
}
ORDER BY ASC(?tbegin)
"""

QUERY_POINT_IN_TIME = """
PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT DISTINCT ?event ?l ?pointintime
WHERE {
    ?event rdf:type sem:Event .
    ?event rdfs:label ?l .
    ?event sem:hasTimeStamp ?pointintime
}
ORDER BY ASC(?pointintime)
"""

QUERY_EVENT_TYPE = """
PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?s ?l ?etl
WHERE {
    ?s ?p ?o .
    ?s rdfs:label ?l .
    ?s sem:eventType ?eventType .
    ?eventType rdfs:label ?etl
}
"""

QUERY_ACTOR_ROLE = """
PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?s ?l ?valreadable ?rolereadable
WHERE {
    ?s ?p ?o .
    ?s rdf:type sem:Event .
    ?s rdfs:label ?l .
    ?s sem:hasActor ?roleType .
    ?roleType rdf:value ?val .
    ?val rdfs:label ?valreadable
    OPTIONAL {?roleType sem:roleType ?role .
                ?role rdfs:label ?rolereadable .}
}
"""
