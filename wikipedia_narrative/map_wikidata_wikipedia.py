"""
Finding Wikipedia page from a Wikidata page
"""

import argparse
import multiprocessing as mp
import pandas as pd
import streamlit as st
from wikipedia_narrative.info_boxes.html_helpers import get_wp_url_from_wd_id

@st.cache(show_spinner=False)
def add_wikipedia_page(df_pd: pd.core.frame.DataFrame,
                       col_wikidata: str,
                       save_path:str = None) -> pd.core.frame.DataFrame:
    """ Adding a wikipedia_page column in the input df_pd.
    If found adds link to English Wikipedia page. Parallelized. """
    num_workers = mp.cpu_count()
    pool = mp.Pool(num_workers)
    df_pd["wikipedia_page"] = pool.map(get_wp_url_from_wd_id,
                                    [x.split("/")[-1] for x in df_pd[col_wikidata].values])
    pool.close()
    pool.join()
    if save_path:
        df_pd.to_csv(save_path)
    return df_pd


def check_args(args: dict):
    """ Checking args in command line to execute script"""
    if (type(args["input"] is str)) and (not args["input"].endswith(".csv")) \
         or (not args["input"].endswith(".csv")):
        raise ValueError("`input`and `output` args should be .csv files, please check")


if __name__ == '__main__':
    # To be executed in shell from `wikipedia_narrative` folder
    # Example of command to execute:
    # python map_wikidata_wikipedia.py -i ../data/events_demo.csv \
    # -o ../data/events_demo_mapped.csv

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", '--input', required=True,
                    help="Input csv path to extract wikidata url from")
    ap.add_argument("-c", "--col", default="event",
                    help="column in input csv corresponding to the wikidata urls")
    ap.add_argument("-o", "--output", default=None,
                    help="Output csv path to save data")
    args_main = vars(ap.parse_args())

    df_main = pd.read_csv(args_main["input"])
    df_main = add_wikipedia_page(df_main, save_path=args_main["output"],
                                 col_wikidata=args_main["col"])
