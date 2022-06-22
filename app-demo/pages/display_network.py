# -*- coding: utf-8 -*-
""" Display network Streamlit page """
from datetime import datetime
import streamlit as st
import pandas as pd
from streamlit_timeline import timeline
from prettytable import PrettyTable

from kb_sparql.local_kg_query import QUERY_EVENT, QUERY_POINT_IN_TIME, \
    QUERY_EVENT_TYPE, QUERY_ACTOR_ROLE
from .helpers import get_session_state_val

def pre_process(node):
    """ URI > more human-readable """
    return node.split("/")[-1].replace('_', ' ')

@st.cache(show_spinner=False)
def pd_to_html(df_pd):
    """ dataframe to html table """

    cols = list(df_pd.columns)[2:]
    t_html = PrettyTable(cols)
    for _, row in df_pd.iterrows():
        t_html.add_row([row[col] for col in cols])
    return t_html.get_html_string()

@st.cache(show_spinner=False)
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

@st.cache(show_spinner=False)
def run_sparql_query(graph, query):
    """ Querying with sparql """
    return list(graph.query(query))

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

    events, event_uris = [], []
    # Retrieving events with begin&end timestamps
    qres_tr = run_sparql_query(graph=graph, query=QUERY_EVENT)
    for row in qres_tr:
        if row.event not in event_uris:
            events.append((row.event, str(row.l), row.tbegin, row.tend))
            event_uris.append(row.event)

    # Retrieving events with points in time (start=end date)
    qres_pit = run_sparql_query(graph=graph, query=QUERY_POINT_IN_TIME)
    for row in qres_pit:
        if row.event not in event_uris:
            events.append((row.event, str(row.l), row.pointintime, None))
            event_uris.append(row.event)

    events.sort(key = lambda x: x[2])
    text_info = get_session_state_val(var="wikipedia_text")

    # Info about event types
    res = run_sparql_query(graph=graph, query=QUERY_EVENT_TYPE)
    info_event_type = pd.DataFrame(columns=["event", "label", "event_type"])
    for row in res:
        data = {'event': [row.s], 'label': [str(row.l)], "event_type": [row.etl]}
        info_event_type = pd.concat([info_event_type, pd.DataFrame(data)], ignore_index=True)
    info_event_type = info_event_type.drop_duplicates()

    # Info about actors and roles
    res = run_sparql_query(graph=graph, query=QUERY_ACTOR_ROLE)
    info_actor = pd.DataFrame(columns=["event", "label", "actor", "role"])
    for row in res:
        data = {'event': [row.s], 'label': [str(row.l)],
                "actor": [row.valreadable], "role": [row.rolereadable]}
        info_actor = pd.concat([info_actor, pd.DataFrame(data)], ignore_index=True)
    info_actor = info_actor.drop_duplicates()


    data = get_timeline_data(events=events, text_info=text_info,
                             info_event_type=info_event_type, info_actor=info_actor)
    timeline(data, height=1500)
