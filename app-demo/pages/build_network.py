# -*- coding: utf-8 -*-
""" Build network Streamlit page """
from datetime import datetime

import pandas as pd
import streamlit as st

from graph_building.converter import WikipediaConverter, WikidataConverter, init_graph
from .helpers import get_session_state_val, check_session_state_value, \
    init_update_session_state

@st.cache(show_spinner=False)
def build_network(df_wp, df_wd):
    """ Build graph with rdf triples """
    graph = init_graph()
    converter_wp = WikipediaConverter()
    graph, counter = converter_wp(graph, df_wp)

    converter_wd = WikidataConverter()
    return converter_wd(graph, df_wd, counter)

def app():
    """ Main app page """
    st.title("Build the network")
    st.markdown("""
    #
    Clicking the button will have the narrative network constructed. 
    
    Extracted info from last steps will be converted to RDF triples.
    """)

    df_wp = get_session_state_val(var="wikipedia_for_graph")
    df_wd = get_session_state_val(var="wikidata_for_graph")

    if isinstance(df_wd, pd.DataFrame) and isinstance(df_wp, pd.DataFrame):

        st.write("##")
        if st.button("Build network"):

            # Populating ontology by converting wikipedia semi-structured data
            # and wikidata triples
            build_start = datetime.now()
            graph, counter = build_network(df_wp=df_wp, df_wd=df_wd)

            if check_session_state_value(var="data_in_cache", value=True):
                init_update_session_state(var="graph", value=graph)
            build_end = datetime.now()

            init_update_session_state(var="build_nt_time",
                                      value=build_end - build_start)
            st.markdown(f"_It took {st.session_state['build_nt_time']} s_")

            st.success("Building done!")
            st.balloons()
