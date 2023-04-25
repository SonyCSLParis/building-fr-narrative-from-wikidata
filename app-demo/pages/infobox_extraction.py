# -*- coding: utf-8 -*-
""" Infobox extraction Streamlit page """
import os
import json
from datetime import datetime
import multiprocessing as mp

import pandas as pd
import yaml
import wptools
from PIL import Image
import streamlit as st


from settings.settings import ROOT_PATH

from wikipedia_narrative.store_page_content import get_page_content
from wikipedia_narrative.info_boxes.get_infobox import extract_infobox_no_url, get_link_from_html, \
    add_url, get_img_src
from wikipedia_narrative.info_boxes.html_helpers import get_html_from_url
from .helpers import init_update_session_state, get_session_state_val, check_session_state_value, \
    add_download_link

with open(os.path.join(ROOT_PATH, "app-demo/content/event_collection.yaml")) as file:
    content = yaml.load(file, Loader=yaml.FullLoader)

def build_df_from_infobox(infoboxes):
    """ Input = infobox dict, output = pandas dataframe """
    df_func = pd.DataFrame(columns=["eventLabel", "predicate", "object", "objectLabel"])
    for event_label, info in infoboxes.items():
        for predicate, curr_info in info.items():
            if curr_info['href']:
                for href in curr_info["href"]:
                    df_func = df_func.append({"eventLabel": event_label, "predicate": predicate,
                                    "object": href, "objectLabel": href},
                                    ignore_index=True)
            else:
                df_func = df_func.append({"eventLabel": event_label, "predicate": predicate,
                                    "object": curr_info['text'], "objectLabel": curr_info['text']},
                                    ignore_index=True)
    return df_func

def check_loaded_data(data: dict[str, dict]):
    """ Check that the input data has the right keys to process further """
    if not data:
        return False
    if any(not isinstance(elt, dict) or not isinstance(k, str) for k, elt in data.items()):
        return False

    return not any("url" not in val or "wikipedia" not in val for _, val in data.items())


@st.cache(show_spinner=False)
def get_one_infobox(wp_page_name: str, url: str, wd_page_name: str,
                    options: list[str], get_image: bool = False):
    """ Searches and return two main elements
    1. Infobox in wikipedia page - if none empty dict.
        options specify any additional preprocessing steps for the infoboxes (cf. in app)
    2. Url links in the infobox if any (scraping and searching for such links) """
    infobox = extract_infobox_no_url(page_name=wp_page_name, options=options)
    html_content = get_html_from_url(url=url)
    links = get_link_from_html(html_content=html_content)

    if get_image:
        return (wd_page_name, add_url(infobox, links), get_img_src(html_content))
    return (wd_page_name, add_url(infobox, links), None)


@st.cache(show_spinner=False)
def get_all_infobox(input_data: dict):
    """ Collecting all infoboxes """
    with mp.Pool(mp.cpu_count()) as pool:
        res = pool.starmap(get_one_infobox,
                        [(x["wikipedia"].split("/")[-1].replace("_", " "),
                            x["wikipedia"],
                            x["event_wd_name"],
                            input_data["options"]) for _, x in input_data["wp_data"].items()])
        pool.close()
        pool.join()

    input_data = input_data["wp_data"]

    for k, infobox, img in res:
        input_data[k]["infobox"] = {k: v for k, v in infobox.items() if k not in ["boxes", "count"]}
        if img:
            input_data[k]['img'] = img
    return input_data


def clean_df(df_input):
    """ Preprocessing of content """
    cols_to_keep = ['eventLabel', 'predicate', 'objectLabel', 'type']
    name_mapping = {
        "Kingdom_of_France_(1791%E2%80%9392)": "Constitutional_Cabinet_of_Louis_XVI"
    }
    replacements = [("%C3%A9", "é"), ("%C3%89", "é"), ("%C3%A8", "è"),
                    ('%C3%A7', 'ç'), ('%C3%8E', "Î"), ("%C3%B4", 'ô'),
                    ("%27", "'"), ("%C3%AB", "ë"), ("%E2%80%93", "-"), ("%C3%A1", "á"),
                    ("%C3%B3", "ó"), ("%C3%AD", "í"), ("%C4%85", "ą"), ("%C3%81", "Á")]

    df_wp = df_input[df_input.object.str.startswith("https")][cols_to_keep]

    df_wp["wptools_name"] = df_wp['objectLabel'] \
        .apply(lambda x: x.split("/")[-1])
    df_wp["wptools_name"] = df_wp['wptools_name'] \
        .apply(lambda x: name_mapping[x] if x in name_mapping else x)

    df_wp = df_wp[~df_wp.wptools_name.str.startswith("index.php")]

    for (pattern, rep) in replacements:
        df_wp['wptools_name'] = df_wp['wptools_name'] \
            .apply(lambda x: x.replace(pattern, rep))

    df_wp['objectLabel'] = df_wp['wptools_name'] \
        .apply(lambda x: " ".join(x.split("/")[-1].split('_')))

    return df_wp

@st.cache(show_spinner=False)
def find_wd_id(name):
    """ Finf Wikidata URI from Wikipedia page name """
    print(name)
    page = wptools.page(name)
    try:
        page.get_parse()
    except:
        return "Q"
    
    if page.data.get('wikibase'):
        return page.data.get('wikibase')
    return "Q"

def add_wd_id(df_wp):
    """ Adding wikidata ID of each Wikipedia feature"""
    mapping = {}
    manual_corrections = {"Marguerite-élie_Guadet": 'Marguerite-Élie_Guadet'}
    content_val = []
    for name in df_wp.wptools_name.values:
        name = manual_corrections[name] if name in manual_corrections else name
        if name in mapping:
            content_val.append(mapping[name])
        else:
            val = find_wd_id(name)
            mapping[name] = val
            content_val.append(val)
    df_wp["wd_id"] = content_val
    return df_wp

def app():
    """ Main func """
    # General introduction

    st.title("Link Extraction")
    st.markdown("""
        #
        ## General presentation
        --- """)

    st.markdown(
        """
        Some Wikipedia pages contain infoboxes. The latters can be described as semi structured data
        with main information about the current page. An example is shown below for the
        [Insurrection of 10 August 1792]
        (https://en.wikipedia.org/wiki/Insurrection_of_10_August_1792).
        In this prototype, information within infoboxes are exploited to retrieve links
        between events, objects and participants.

        In the example below, `Date`, `Location` and `Result` for instance
        are considered infobox labels.
        The content of the infobox label `Date` would be `10 August, 1792`."""
    )
    st.image(Image.open(os.path.join(ROOT_PATH, "app-demo/images/infobox-ex.png")))

    st.markdown(
        """
        Use the button below to extract infoboxes from Wikipedia pages.

        Some additional preprocessing steps were added:

        1. Only keep relevant infobox labels for the narrative
            (_filter on infobox label value_)

        2. Merge similar infobox labels
        (_in this narrative context, some labels carry the same information, hence they are unified under one single name_)

        """
    )

    with st.expander("Find out more about the options described above"):
        st.markdown(
                    """
                    |  Number | Type  | Description |
                    |---|---|---|
                    | 1 | Only keep relevant infobox labels for the narrative | Filtering on infobox label values. Labels relevant for this prototype were determined manually |
                    | 2 | Merge similar infobox labels  | In the frame of this prototype, some labels carry the same information, hence they are unified under one single name |
                    \n
                    """
                    )
        st.write("#")
        st.write("### Infobox labels throughout all retrieved instances")
        st.image(Image.open(os.path.join(ROOT_PATH, "app-demo/images/grouped-infobox-labels.png")))
        st.write("#")
        st.write("### Merging process")
        st.write("Labels that were kept for the prototype")
        st.image(Image.open(os.path.join(ROOT_PATH, "app-demo/images/merge-labels-keep.png")))
        st.write("Labels that were discarded for the prototype")
        st.image(Image.open(os.path.join(ROOT_PATH, "app-demo/images/merge-labels-discard.png")))


    st.markdown("""
        #
        ## Infobox extraction
        --- """)
    options = ["1", "2"]

    # Extracting infobox from several input wikipedia pages
    df_wd = get_session_state_val(var="wikidata_collected")

    if st.button("Get Info boxes"):
        data, not_found_events = get_page_content(
            df_input=df_wd, col_main_name=content["col_main_name"],
            col_wd_name=content['col_wikidata'], col_wp_name="wikipedia_page",
            col_query_type="query_type", pointintime=content['pointintime'],
            extract_text=True)

        if check_session_state_value(var="data_in_cache", value=True):
            init_update_session_state(var="wikipedia_text",
                value={k: info['content'].split('==')[0] for k, info in data.items()})

        st.markdown(f"""
        #
        The following IDs could not be mapped to any Wikipedia pages: 
        
        {', '.join(not_found_events)}""")

        if data is not None:

            if isinstance(data, dict):
                if not check_loaded_data(data):
                    st.error("Please load a valid dict structure to extract infoboxes: " + \
                        "1. Non-empty 2. Keys = strings, values = dictionary ")

                else:
                    collect_start = datetime.now()
                    new_data = get_all_infobox(input_data={"options": options, "wp_data": data})
                    collect_end = datetime.now()
                    st.write(
                        "_Extracting all infoboxes from Wikipedia pages took: " + \
                            f"{collect_end - collect_start} s_")

                    np_page = len(new_data)
                    nb_infobox = len([val["infobox"] for _, val in new_data.items() \
                        if val["infobox"]])

                    st.markdown(
                    f"""
                    |  Type | Nb  | % of all instances collected |
                    |---|---|---|
                    |  All Wikipedia pages | {np_page}  | 100 |
                    | Wikipedia pages with infobox  | {nb_infobox}  | {round(100*nb_infobox/np_page, 1)}  |
                    \n
                    """
                    )

                    if check_session_state_value(var="data_in_cache", value=True):
                        init_update_session_state(var="infobox_collected", value=new_data)

                    st.write("#")
                    with st.expander("Display all data"):
                        st.json(new_data)
                    with st.expander("Display infoboxes only"):
                        st.json({k: v["infobox"] for k, v in new_data.items()})

                    add_download_link(to_download=json.dumps(new_data, indent=4).encode(),
                                    file_end_name="collected-infoboxes", extension="json")
                    st.write("#")

                    i_filter = [''] + [i for i in range(1,15)]

                    pred_grouping_wp = {
                        'who': [f"{x}{i}" for x in \
                            ['Participants', 'appointer', 'combatant', 'commander', 'commanders',
                            'deputy', "founder", "house", "leader", "legislature", "organisers",
                            "p", "participants", "precursor"] for i in i_filter],
                        'where': [f"{x}{i}" for x in \
                            ['Location', 'area', 'coordinates', "location", "place"] \
                                for i in i_filter],
                        'when': [f"{x}{i}" for x in \
                            ['Date', 'abolished', 'date', 'date_end', 'date_event', 'date_pre',
                            'date_start', 'defunct', 'disbanded', 'established', "formation",
                            "founded_date", "life_span", 'year_'] for i in i_filter],
                        'temporal_link': [f"{x}{i}" for x in \
                            ["era", "event", "event_end", "event_pre", "event_start", "partof",
                            "preceded_by", "succeeded_by", "succession"] for i in i_filter],
                        'causal_link': [f"{x}{i}" for x in \
                            ['Result', 'cause', 'outcome', 'result', 'territory'] \
                                for i in i_filter],
                    }

                    inverse_pred_wp = {x: k for k, v in pred_grouping_wp.items() for x in v}

                    infoboxes = {k: v['infobox'] for k, v in new_data.items()}
                    df_wp = build_df_from_infobox(infoboxes).drop_duplicates()

                    if check_session_state_value(var="data_in_cache", value=True):
                        init_update_session_state(var="wikipedia_collected", value=df_wp)

                    df_filter_wp  = df_wp[df_wp.predicate.isin(
                        [x for _, v in pred_grouping_wp.items() for x in v])].copy()
                    df_filter_wp['type'] = df_filter_wp.predicate \
                        .apply(lambda x: inverse_pred_wp[x])

                    st.markdown(f"""
                    #
                    Some figures on the extracted info boxes:

                    * {df_wp.eventLabel.unique().shape[0]}: Number of events with an info box
                    * {df_filter_wp.eventLabel.unique().shape[0]}: Number of events that contain a infobox
                    with at least one useful information for the narrative
                    #
                    """)


                    info =  df_filter_wp.groupby(['eventLabel', 'type']) \
                        .agg({'object': 'count'}).reset_index()
                    st.caption("Number of types of links for each event")
                    st.write(info)

                    st.caption('Number of events and unique events per type of narrative information')
                    st.write(
                        df_filter_wp.groupby(['type']) \
                            .agg({'eventLabel': ['count', 'nunique']}).reset_index()
                    )

                    # Extracting info from each feature in Wikipedia
                    st.write("## Necessary information to extract triples")
                    df_wp = clean_df(df_input=df_filter_wp)
                    df_wp = add_wd_id(df_wp)

                    df_wd = get_session_state_val(var="wikidata_collected") \
                        [["event", "eventLabel"]] \
                            .rename(columns={"event": "wd_page"})
                    df_wp = df_wp.merge(df_wd, how='left', on='eventLabel')
                    df_wp["obj_wd"] = df_wp["wd_id"] \
                        .apply(lambda x: f"http://www.wikidata.org/entity/{x}")
                    df_wp = df_wp.drop_duplicates()
                    st.write(df_wp)
                    add_download_link(to_download=df_wp.to_csv(index=False).encode(),
                          file_end_name="collected-wikipedia-data-for-triples", extension="csv")

                    if check_session_state_value(var="data_in_cache", value=True):
                        init_update_session_state(var="wikipedia_for_graph", value=df_wp)
