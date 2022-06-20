# -*- coding: utf-8 -*-
"""
Streamlit page: collecting events
"""

import os
import yaml
import streamlit as st

from settings.settings import ROOT_PATH
from .helpers import collect_data_st, display_html_graph


with open(os.path.join(ROOT_PATH, "app-demo/content/event_collection.yaml")) as file:
    content = yaml.load(file, Loader=yaml.FullLoader)


def app():
    """ Main app function """
    # General introduction
    st.title("Event Collection")
    st.markdown("""
        #
        ## General presentation
        --- """)
    st.markdown(
        """
        The aim of this demo was to study the French Revolution.

        Several types of nodes were taken into account for this pilot:
        * <event> **part of** <French Revolution>
        * <French Revolution> **has significant event** <event>
        * <event> **is instance of** <historical country>
        and **has country** <France>

        An additional filter was added to extract events in the right time range.
        """
    )

    display_html_graph(html_path=os.path.join(ROOT_PATH,
                                              f"app-demo/graph-html/{content['graph_doc']}.html"),
                       size=550)

    st.write('Select the paths that you want to use for event collection:')
    collect_data_st(content=content)
