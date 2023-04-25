# -*- coding: utf-8 -*-
""" Wikidata info retrieval """
import os
import yaml
import streamlit as st
import pandas as pd
from settings.settings import ROOT_PATH

from kb_sparql.query_db import SPARQL_QUERIES
from kb_sparql.sparql_query import run_query_return_df
from .helpers import get_session_state_val, add_download_link
from .helpers import check_session_state_value, init_update_session_state

with open(os.path.join(ROOT_PATH, "app-demo/content/event_collection.yaml")) as file:
    content = yaml.load(file, Loader=yaml.FullLoader)

query_template = SPARQL_QUERIES['forward_links']

def get_clean_output_sparql(id_event):
    """ Rename columns from sparql output """
    to_keep = ["objectLabel.value", "wdLabel.value", "ps_.value", "ps_Label.value"]
    renaming = {
        "objectLabel.value": "eventLabel", "wdLabel.value": "predicate",
        "ps_.value": "object", "ps_Label.value": "objectLabel"
    }
    return_df = run_query_return_df(query_template(id_event))[to_keep].rename(columns=renaming)
    return_df['wd_page'] = f"http://www.wikidata.org/entity/{id_event}"
    return return_df

@st.cache(show_spinner=False)
def get_outgoing_nodes(events):
    """ SPARQL Query for outgoing nodes """
    df_wd = pd.DataFrame(columns=["wd_page", "eventLabel", "predicate", "object", "objectLabel"])
    for event in events:
        id_event = event.split('/')[-1]
        df_wd = pd.concat([df_wd, get_clean_output_sparql(id_event)])
    return df_wd

def app():
    """ Main func """
    # General introduction

    st.title("Wikidata Enrichment")
    st.markdown("""
        #
        ## Extracting outgoing nodes of each event.
        --- 
        This step will extract all outgoing triples for each event collected at Step 1.

        For an event e, an outgoing triple is a triple `(subject, predicate, object)`
        where the `subject` is the event `e`. 
        
        Later on for building the narrative, predicates linking to relevant information 
        were manually defined. Such predicates should link to either a person, a location, 
        a timestamp, or a causal or temporal link between events. 
        """)

    data = get_session_state_val(var="wikidata_collected")

    if st.button("Extract outgoing nodes"):

        df_wd = get_outgoing_nodes(events=data.event.values)
        add_download_link(to_download=df_wd.to_csv(index=False).encode(),
                          file_end_name="collected-wikidata", extension="csv")

        if check_session_state_value(var="data_in_cache", value=True):
            init_update_session_state(var="wikidata_for_graph", value=df_wd)

        pred_grouping_wd = {
            'who': ['participant', 'organizer', 'founded by'],
            'where': ['country', 'location', 'coordinate location',
                    'located in the administrative territorial entity', 'continent'],
            'when': ['point in time', 'start time', 'end time',
                    'inception', 'dissolved, abolished or demolished date'],
            'temporal_link': ['part of', 'followed by', 'replaces',
                            'replaced by', 'follows', 'time period'],
            'causal_link': ['has effect'],
        }

        inverse_pred_wd = {x: k for k, v in pred_grouping_wd.items() for x in v}
        predicates_narrative_wd = [x for _, v in pred_grouping_wd.items() for x in v]

        df_filter_wd  = df_wd[df_wd.predicate.isin(
            [x for _, v in pred_grouping_wd.items() for x in v])].copy()
        df_filter_wd['type'] = df_filter_wd.predicate.apply(lambda x: inverse_pred_wd[x])

        st.markdown(f"""
        #
        Some figures on the extracted triples:

        * {len(predicates_narrative_wd)}: Number of predicates manually selected
        that contain relevant information for the narratives
        * {df_wd.shape[0]}: Number of triples extracted for all events
        * {df_wd[df_wd.predicate.isin(predicates_narrative_wd)].shape[0]}: Number of triples
        with relevant information for the narrative
        * {df_wd.wd_page.unique().shape[0]}: Number of events for the narrative
        * {df_filter_wd.wd_page.unique().shape[0]}: Number of events that contain at least one
        useful information triple for the narrative
        #
        """)

        with st.expander("More information on the filtered predicates"):
            st.markdown("\n".join(
                [f"* {k}: {[elt for elt in v]}" for k, v in pred_grouping_wd.items()]
            ))

        st.write("#")
        info =  df_filter_wd.groupby(['eventLabel', 'type']).agg({'object': 'count'}).reset_index()
        st.caption('Number of types of links for each event')
        st.write(info)
        st.write("#")
        st.caption('Number of events and unique events per type of narrative information')
        st.write(
            df_filter_wd.groupby(['type']) \
                .agg({'eventLabel': ['count', 'nunique']}) \
                    .reset_index()
        )
