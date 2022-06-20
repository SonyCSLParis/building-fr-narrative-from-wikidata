# -*- coding: utf-8 -*-
"""
Backend helpers for the streamlit app
"""

import base64
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from wikipedia_narrative.map_wikidata_wikipedia import add_wikipedia_page
from kb_sparql.gather_events import build_args_for_collect, collect_data
from .vis import get_fig_hist_plotly


def init_update_session_state(var, value):
    """ Initializing a cached value """
    st.session_state[var] = value


def check_session_state_value(var, value):
    """ Comparing cached value and value """
    return st.session_state[var] == value


def check_val_in_session_state(var):
    """ Checking var is cached or not """
    return var in st.session_state


def get_session_state_val(var):
    """ Get cached value """
    return st.session_state[var]


def add_download_link(to_download, file_end_name: str, extension: str):
    """ Clickable link to have some content downloaded """
    b64 = base64.b64encode(to_download).decode()
    save_date = str(datetime.now())
    file_name = f"{save_date[:10]}-{save_date[11:19]}-{file_end_name}.{extension}"
    linko= f'<a href="data:file/{extension};base64,{b64}" ' + \
        f'download="{file_name}">Download {extension} file</a>'
    st.markdown(linko, unsafe_allow_html=True)

def collect_data_st(content: dict):
    """ Select type of graph path to use """
    paths = st.multiselect(
        f"Choose the types of {content['type_data']} you want to retrieve",
        list(content['path_for_event'].keys())
    )
    if not paths:
        st.markdown("""
        #
        #
        #
        """)
        st.error("Please select at least one path.")


    # Select type of data to collect
    # 1. Wikidata Only
    # 2. 1. + Adding a column to map each wikidata page to a wikipedia one
    # 3. 2. + Retrieving text content from Wikipedia pages

    if st.button("Collect events"):

        # Collect data from Wikidata
        id_query_type_l = [(content['path_for_event'][path]["id"],
                            content['path_for_event'][path]["query_type"],
                            content["year_begin"], content["year_end"]) \
                            for path in paths]
        collect_start = datetime.now()
        df_wd = collect_data(
            args_collect_list=build_args_for_collect(id_query_type_l)) \
                .drop_duplicates()
        df_wd = df_wd.fillna("")
        collect_end = datetime.now()


        # Add Wikipedia info
        df_wd = add_wikipedia_page(df_wd, col_wikidata=content["col_wikidata"],
                                save_path=None)
        collect_end = datetime.now()

        init_update_session_state(var=content["session_state_wd"],
                                  value=collect_end - collect_start)

        st.markdown("""
        #
        ## Collected data and figures
        --- """)

        it_took =  \
            "Collecting data from Wikidata and scraping Wikipedia urls"
        st.markdown(f"_{it_took} took:\n {st.session_state[content['session_state_wd']]} s_")


        # Output result
        paginate(df_wd, session_state_var_page=content["session_state_var_page"],
                 max_nb=content["max_nb"])
        add_download_link(to_download=df_wd.to_csv(index=False).encode(),
                          file_end_name="collected-data", extension="csv")


        # Visualisations (type of events, duplicates events, type of instances)
        st.plotly_chart(
            figure_or_data=get_fig_hist_plotly(
                df_input=df_wd, x_data="query_type",
                tickangle=45, title="Distribution of types of events retrieved from Wikidata"),
                use_container_width=True)

        df_nb_query_type = df_wd.groupby(content["col_wikidata"]).agg({'query_type': "nunique"})
        df_nb_query_type = df_nb_query_type[df_nb_query_type.query_type > 1]
        df_filtered = df_wd[df_wd[content["col_wikidata"]]\
            .isin(df_nb_query_type.index)][[content['col_main_name'], 'query_type']]

        if df_filtered.shape[0] > 1:
            st.write("Some instances could be retrieved with two different query types. " + \
                "Below is the list of such instances:")
            st.dataframe(
                df_filtered.pivot_table(
                    index=content['col_main_name'], columns='query_type', aggfunc=len))

        st.write("Recap of instances collected")

        curr_df = df_wd[[col for col in df_wd \
            if col in ['event', 'eventLabel', 'wikipedia_page']]]
        nb_all  = curr_df.shape[0]
        curr_df = curr_df.drop_duplicates()
        nb_unique = curr_df.shape[0]
        curr_df = curr_df[~curr_df[content['col_main_name']].str.contains('Q[1-9]')]
        nb_label = curr_df.shape[0]
        nb_mapped = len([url for url in curr_df.wikipedia_page if url != ""])

        st.markdown(
            f"""
            |  Type | Nb  | % of all instances collected |
            |---|---|---|
            |  All collected instances | {nb_all}  | 100 |
            | Unique collected instances  | {nb_unique}  | {round(100*nb_unique/nb_all, 1)}  |
            | Unique collected instances with labels | {nb_label}  | {round(100*nb_label/nb_all, 1)}  |
            | Unique collected instances with labels and Wikipedia mapping  | {nb_mapped}  | {round(100*nb_mapped/nb_all, 1)}  |
            \n
            """
        )
        st.markdown("\n\n")

        if check_session_state_value(var="data_in_cache", value=True):
            init_update_session_state(var="wikidata_collected", value=df_wd)


def display_html_graph(html_path: str, size: int):
    """ Display html graph """
    html_file = open(html_path, 'r', encoding='utf-8')
    source_code = html_file.read()
    components.html(source_code, height=size, width=size)


def paginate(df_pd: pd.core.frame.DataFrame, session_state_var_page: str, max_nb: int):
    """
    Pagination code found in one of streamlit demos:
    https://github.com/streamlit/release-demos/blob/0.84/0.84/demos/pagination.py
    """
    if session_state_var_page not in st.session_state:
        st.session_state[session_state_var_page] = 0

    col1, col2, col3, _ = st.columns([0.1, 0.17, 0.1, 0.63])

    def next_page():
        st.session_state[session_state_var_page] += 1

    def prev_page():
        st.session_state[session_state_var_page] -= 1

    if st.session_state[session_state_var_page] < df_pd.shape[0] // max_nb:
        col3.button(">", on_click=next_page)
    else:
        col3.write("")  # this makes the empty column show up on mobile

    if st.session_state[session_state_var_page] > 0:
        col1.button("<", on_click=prev_page)
    else:
        col1.write("")  # this makes the empty column show up on mobile

    col2.write(f"Page {1+st.session_state[session_state_var_page]}" + \
        f" of {df_pd.shape[0] // max_nb + 1}")
    start = max_nb * st.session_state[session_state_var_page]
    st.write("")
    st.dataframe(df_pd.iloc[start:start+max_nb])
