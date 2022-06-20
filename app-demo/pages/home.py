# -*- coding: utf-8 -*-
""" Home page of the app """

import os
import streamlit as st
from PIL import Image
from settings.settings import ROOT_PATH

def app():
    """ Main func """
    st.title("Extracting a French Revolution Narrative Graph from Wikidata and Wikipedia")
    st.write("#")

    col1, col2, col3 = st.columns(3)

    images = [Image.open(path) for \
                path in [os.path.join(ROOT_PATH, f"app-demo/images/{fn}.jpg") for \
                    fn in ["tennis_court_oath", "storming_of_the_bastille",
                            "execution_of_louis_xvi"]]]
    captions = ["Tennis Court Oath - June 20th, 1789",
                "Storming of the Bastille - July 14th, 1789",
                "Execution of Louis XVI - January 21st, 1793"]
    cols = [col1, col2, col3]

    for i, image in enumerate(images):
        cols[i].image(image, caption=captions[i], use_column_width=True)

    st.markdown(
        """
        ## What
        This web interface enables to collect data from Wikidata and Wikipedia
        to build narratives. The focus is on the French Revolution.

        ## Why
        This demo enables a user and a machine to interact to build
        a narrative timeline of the French Revolution.
        The user's inputs help the machine select the nodes to extract
        for the narrative,
        whereas the timeline output can enhance the reader's knowledge about this historical topic.

        ## How
        To run this demo entirely, you should go to every
        Navigation page (see left column menu) in order:

        1. **Event Collection.** the user can select the paths to extract the events from
        2. **Wikidata Enrichment.** retrieving outgoing nodes of each event from Wikidata
        3. **Link Extraction.** for each event that has a pointer to a Wikipedia page,
        the infobox information is retrieved if there is any. This step might take a bit longer.
        4. **Build Network.** from the data collected, RDF triples are constructed
        5. **Display Network.** Visualisation of the French Revolution narrative as a timeline
        #
        """
    )

    with st.expander("Useful Links"):
        st.markdown(
            """
            1. [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page)
            2. [Wikipedia](https://www.wikipedia.org)
            3. [Streamlit](https://streamlit.io)
            """
        )

    credits_image = [
        "Tennis Court Oath:  https://www.connaissancedesarts.com/arts-expositions/" + \
            "le-serment-du-jeu-de-paume-de-david-etude-dun-chef-doeuvre-11142980/ \n",
        "Storming of the Bastille: https://fr.wikipedia.org/wiki/Révolution_française \n",
        "Execution of Louis XVI: https://www.lelivrescolaire.fr/page/16858685 \n"]

    with st.expander("Image Credits"):
        st.markdown("\n".join(credits_image))
