# -*- coding: utf-8 -*-
"""
Extract text from Wikipedia page
"""
import json
import argparse
import multiprocessing as mp
import pandas as pd
import streamlit as st
from wikipedia_narrative.wikipedia_page import WikipediaPage


def get_info_from_one_event(row: pd.core.series.Series, col_main_name: str,
                            col_wp_name: str, col_wd_name: str,
                            col_query_type: str, pointintime: str, extract_text: bool) -> dict:
    """ Extracting wikipedia text content from one Wikidata Node if extract_text
    Else only returns info in dict-like structure.
    row corresponds to one row of the output of the sparql query """
    event_wd = row[col_main_name]
    try:
        event_wp = row[col_wp_name].split("/")[-1].replace("_", " ")
        page = WikipediaPage(title=event_wp)
        res = {"content": page.content, "url": page.url,
               "event_wd_name": event_wd, "event_wp_name": event_wp,
               "wikidata": row[col_wd_name], "wikipedia": row[col_wp_name],
               "query_type": row[col_query_type]} if extract_text else \
                   {"url": page.url,
                    "event_wd_name": event_wd, "event_wp_name": event_wp,
                    "wikidata": row[col_wd_name], "wikipedia": row[col_wp_name],
                    "query_type": row[col_query_type]}

        res.update({k: row[v] for (k, v) in \
            [("pointintime", pointintime)] if v})
        return res
    except Exception as exception:
        print(f"=={exception}\nEvent {event_wd} could not" + \
            " be searched through the wikipedia module\n==")
        return dict(event_wd_name=event_wd)


@st.cache(allow_output_mutation=True, show_spinner=False)
def get_page_content(df_input: pd.core.frame.DataFrame, col_main_name: str,
                     col_wd_name: str, col_wp_name: str,
                     col_query_type: str, pointintime: str, extract_text: bool) -> dict[str, dict]:
    """ [Optional] Getting wikipedia text content from all rows in input df_input +
    [All] Formatting text output"""
    num_workers = mp.cpu_count()
    pool = mp.Pool(num_workers)
    res = pool.starmap(get_info_from_one_event,
                       [(row, col_main_name, col_wp_name, col_wd_name,
                         col_query_type, pointintime, extract_text) \
                            for _, row in df_input.iterrows()])
    pool.close()
    pool.join()

    return {x["event_wd_name"]: x for x in res if len(x.keys()) > 1}, \
        [x["event_wd_name"] for x in res if len(x.keys()) == 1]


def check_args(args):
    """ Checking args in command line to execute script"""
    if not args["input"].endswith(".csv"):
        raise ValueError("`input` params should be a .csv file")

    if (isinstance(args['output'], str)) and (not args["output"].endswith(".json")):
        raise ValueError("`output` params should be a .json file")


if __name__ == '__main__':
    """
    To be executed in shell from `wikipedia_narrative` folder
    Example of command to execute:
    python store_page_content.py -i ../data/events_demo_mapped.csv -o ../data/events_content.json
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", '--input', required=True,
                    help="Input csv path to extract list of events")
    ap.add_argument("-cen", "--col_main_name", default="eventLabel",
                    help="column in input csv corresponding to the event names")
    ap.add_argument("-cwdn", "--col_wd_name", default="event",
                    help="column in input csv corresponding to the wikidata links")
    ap.add_argument("-cwpn", "--col_wp_name", default="wikipedia_page",
                    help="column in input csv corresponding to the wikipedia pages")
    ap.add_argument("-cqt", "--col_query_type", default="query_type",
                    help="column in input csv corresponding to the query_type")
    ap.add_argument("-p", "--pointintime", default="pointintime",
                    help="column in input csv corresponding to the pointintime")
    ap.add_argument("-o", '--output', default=None,
                    help="Output json path to store extracted content")
    ARGS = vars(ap.parse_args())


    info, _ = get_page_content(df_input=pd.read_csv(ARGS["input"]),
                               col_main_name=ARGS["col_main_name"],
                               col_wd_name=ARGS["col_wd_name"],
                               col_wp_name=ARGS["col_wp_name"],
                               col_query_type=ARGS['col_query_type'],
                               pointintime=ARGS["pointintime"],
                               extract_text=True)
    if ARGS['output']:
        json.dump(info, open(ARGS['output'], "w"), indent = 4)
    