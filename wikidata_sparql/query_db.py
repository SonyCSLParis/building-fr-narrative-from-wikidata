"""
SPARQL_QUERIES:
- keys: naming used through the repo for specific SPARQL queries
- values: function taking a wikidata ID (str) as input and returning a string SPARQL query
"""

SPARQL_QUERIES = {
    "forward_links": lambda id: \
        """
        SELECT ?objectLabel ?wdLabel ?ps_ ?ps_Label {
            VALUES (?object) {(wd:""" + id + """)} """ + \
            """
            ?object ?p ?statement .
            ?statement ?ps ?ps_ .

            ?wd wikibase:claim ?p.
            ?wd wikibase:statementProperty ?ps.

            OPTIONAL {
            ?statement ?pq ?pq_ .
            ?wdpq wikibase:qualifier ?pq .
            }

            SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
        } ORDER BY ?wd ?statement ?ps_
        """,

    "incoming_links": lambda id: \
        """
        SELECT ?objectLabel ?wdLabel ?ps_Label {
            VALUES (?ps_) {(wd:""" + id + """)} """ + \
            """
            ?object ?p ?statement .
            ?statement ?ps ?ps_ .

            ?wd wikibase:claim ?p.
            ?wd wikibase:statementProperty ?ps.

            OPTIONAL {
            ?statement ?pq ?pq_ .
            ?wdpq wikibase:qualifier ?pq .
            }

            SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
        } ORDER BY ?wd ?statement ?ps_
        """,

    "obj-part-of-id": lambda id: \
        """
        SELECT ?event ?eventLabel ?pointintime ?start ?end ?inception ?dissolved
        WHERE {
        ?event wdt:P361 wd:""" + id + """. """ + \
        """
        OPTIONAL { ?event wdt:P585 ?pointintime. }
        OPTIONAL { ?event wdt:P580 ?start. }
        OPTIONAL { ?event wdt:P582 ?end. }
        OPTIONAL { ?event wdt:P571 ?inception. }
        OPTIONAL { ?event wdt:P576 ?dissolved. }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
        }
        """,

    "obj-instance-of-historical-country-and-has-country-id": lambda input: \
        """
        SELECT ?event ?eventLabel ?inception ?end
        WHERE {
        ?event wdt:P31 wd:Q3024240;
               wdt:P17 wd:""" + input["id"] + """. """ + \
        """
        OPTIONAL { ?event wdt:P571 ?inception. }
        OPTIONAL { ?event wdt:P576 ?end. }
        FILTER (('""" + input["year_begin"] + """-01-01T00:00:00+00:00'^^xsd:dateTime < ?inception && ?inception < '""" + input["year_end"] + """-12-31T00:00:00+00:00'^^xsd:dateTime) ||
                ('""" + input["year_begin"] + """-01-01T00:00:00+00:00'^^xsd:dateTime < ?end && ?end < '""" + input["year_end"] + """-12-31T00:00:00+00:00'^^xsd:dateTime))
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
        }
        """,  # Q142 = France

    "id-has-significant-event-obj": lambda id: \
        """
        SELECT ?event ?eventLabel ?pointintime ?start ?end ?inception ?dissolved
        WHERE {
        wd:""" + id + """ wdt:P793 ?event.
        OPTIONAL { ?event wdt:P585 ?pointintime. }
        OPTIONAL { ?event wdt:P580 ?start. }
        OPTIONAL { ?event wdt:P582 ?end. }
        OPTIONAL { ?event wdt:P571 ?inception. }
        OPTIONAL { ?event wdt:P576 ?dissolved. }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
        }
        """,

    "p-participant-in-id": lambda id: \
        """
        SELECT ?p ?pLabel
        WHERE {
        ?p wdt:P1344 wd:""" + id + """. """ + \
        """
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
        }
        """,
}
