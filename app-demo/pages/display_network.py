""" Display network Streamlit page """
from datetime import datetime
import streamlit as st
import pandas as pd
from streamlit_timeline import timeline
from prettytable import PrettyTable

from .helpers import get_session_state_val

def pre_process(node):
    """ URI > more human-readable """
    return node.split("/")[-1].replace('_', ' ')

def pd_to_html(df_pd):
    """ dataframe to html table """

    cols = list(df_pd.columns)[2:]
    t_html = PrettyTable(cols)
    for _, row in df_pd.iterrows():
        t_html.add_row([row[col] for col in cols])
    return t_html.get_html_string()

def get_timeline_data(events, text_info, info_event_type, info_actor):
    """ Timeline data in order """
    data = {
        "title": {
            "text": {"headline": "French Revolution Timeline"}
        },
        "events": []
    }
    for _, label, start, end in events:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        curr_info = {
            "text": {"headline": label},
            "start_date": {"year": start_date.year,
                           "month": start_date.month, "day": start_date.day}
        }
        if end:
            end_date = datetime.strptime(end, "%Y-%m-%d")
            curr_info["end_date"] = {
                "year": end_date.year,
                "month": end_date.month, "day": end_date.day
            }

        text = []
        if label in text_info:
            text.append(f"<p>{text_info[label]}</p>")

        event_type = info_event_type[info_event_type.label == label]
        if event_type.shape[0] > 0:
            text.append(pd_to_html(event_type))

        actors = info_actor[info_actor.label == label]
        if actors.shape[0] > 0:
            text.append(pd_to_html(actors))

        curr_info["text"]["text"] = "\n".join(text)
        data["events"].append(curr_info)
    return data


def app():
    """ Main func """
    st.title("Display networks")

    st.markdown("""
        #
        ## General presentation
        --- 

        This section will display the narrative timeline that was built with this interface.
        """)

    graph = get_session_state_val(var="graph")
    graph_csv = pd.DataFrame(columns=["subject", "predicate", "object"])
    for (sub, pred, obj) in graph:
        data = {'subject': [sub], 'predicate': [pred], "object": [obj]}
        graph_csv = pd.concat([graph_csv, pd.DataFrame(data)], ignore_index=True)

    events = []

    query_tr = """
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
    qres_tr = graph.query(query_tr)
    event_uris = []
    for row in qres_tr:
        if row.event not in event_uris:
            events.append((row.event, str(row.l), row.tbegin, row.tend))
            event_uris.append(row.event)

    query_pit = """
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
    qres_pit = graph.query(query_pit)
    for row in qres_pit:
        if row.event not in event_uris:
            events.append((row.event, str(row.l), row.pointintime, None))
            event_uris.append(row.event)

    events.sort(key = lambda x: x[2])
    text_info = get_session_state_val(var="wikipedia_text")

    res = graph.query(
        """
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
    )
    info_event_type = pd.DataFrame(columns=["event", "label", "event_type"])
    for row in res:
        data = {'event': [row.s], 'label': [str(row.l)], "event_type": [row.etl]}
        info_event_type = pd.concat([info_event_type, pd.DataFrame(data)], ignore_index=True)
    info_event_type = info_event_type.drop_duplicates()


    res = graph.query(
        """
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
    )
    info_actor = pd.DataFrame(columns=["event", "label", "actor", "role"])
    for row in res:
        data = {'event': [row.s], 'label': [str(row.l)],
                "actor": [row.valreadable], "role": [row.rolereadable]}
        info_actor = pd.concat([info_actor, pd.DataFrame(data)], ignore_index=True)
    info_actor = info_actor.drop_duplicates()


    data = get_timeline_data(events=events, text_info=text_info,
                             info_event_type=info_event_type, info_actor=info_actor)
    timeline(data, height=1500)
