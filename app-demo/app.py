"""
Main app sript for the streamlit web interface:
Home: describing the project
1. Event Collection: collect data from wikidata (events)
2. Link Extraction: Extracting semi structured data from Wikipedia (infoboxes)
3. Build Network: ~ Narrative Network
4. Display Network: Visualising the steps of network construction
"""

import streamlit as st
from pages import event_collection, home, infobox_extraction, \
    build_network, display_network, wikidata_retrieval

PAGES = {
    "Home": home,
    "1. Event Collection": event_collection,
    "2. Wikidata Enrichment": wikidata_retrieval,
    "3. Link Extraction": infobox_extraction,
    "4. Build Network": build_network,
    "5. Display Network": display_network
}

st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
st.session_state["data_in_cache"] = True

page = PAGES[selection]
page.app()
