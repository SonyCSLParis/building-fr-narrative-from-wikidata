# -*- coding: utf-8 -*-
""" Querying KG with SPARQL queries """
import re
import argparse
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON

from kb_sparql.query_db import SPARQL_QUERIES
from settings.settings import AGENT


def run_query_return_df(query: str, sparql_endpoint: str = \
        "https://query.wikidata.org/sparql") -> pd.core.frame.DataFrame:
    """ Executing input SPARQL query
    and returning results in dataframe format """
    sparql = SPARQLWrapper(sparql_endpoint,
                           agent=AGENT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return pd.json_normalize(results['results']['bindings'])


def get_col_to_keep(query: str) -> list[str]:
    """ Retrieving columns to keep from sparql query output in DataFrame format format """
    pattern = "SELECT (.+?) ({|WHERE)"
    matches = re.search(pattern, query.replace("\n", " "))
    if not matches:
        raise ValueError(("Problem with the query"))
    return [elt.strip() for elt in matches.group(1).split("?") if elt != '']


def process_df(df_input: pd.core.frame.DataFrame, query:str) -> pd.core.frame.DataFrame:
    """ Cleaning DataFrame output of sparql query
    1. Only keeping columns specified in sparql query
    2. Renaming columns """
    cols = get_col_to_keep(query)
    df_input = df_input[[col for col in df_input.columns if col.endswith(".value")]]
    df_input = df_input.rename(columns={col: col.replace(".value", "") for col in df_input.columns})
    return df_input[[col for col in cols if col in df_input.columns]]


def get_output_sparql(query:str, clean_df:bool = 1, save_path:str = None):
    """ Running SPARQL query, getting dataframe output and
    1. Clean it if clean_df
    2. Save it if save_path """
    df_f = run_query_return_df(query)
    if df_f.shape[0] == 0:
        return None
    df_f = process_df(df_f, query) if clean_df else df_f
    if save_path:
        df_f.to_csv(save_path)
    return df_f


def check_args(args: dict):
    """ Checking args in command line to execute script"""
    if (args["id"]) and (args['query_type'] not in SPARQL_QUERIES):
        raise ValueError("Query type currently not handled, please retry. " + \
            "Queries types are the keys in the SPARQL_QUERIES dictionnary.")

    if args['clean_df'] not in ['0', '1', 0, 1]:
        raise ValueError("Please check your argument, should be 1 or 0")

    if args['save_path']:
        path = args['save_path']
        if not isinstance(path, str) or not path.endswith(".csv"):
            raise ValueError("Save path must be a string ending with .csv, please retry")

    if (not args["id"] and (not args["path"] or not args["column"])) or \
        (args["id"] and args["path"] and args["column"]):
        raise ValueError("Either `id` should be specified, or " + \
            "`path` and `column`, but not the three of them")


def main(args):
    """ Main func when executing script """
    if args["id"]:  # Running one SPARQL query type from one ID
        df_output = get_output_sparql(query=SPARQL_QUERIES[args['query_type']](args['id']),
                                      clean_df=int(args["clean_df"]),
                                      save_path=args["save_path"])
        if isinstance(df_output, pd.DataFrame):
            df_output['query_type'] = args['query_type']

    else:  # taking ids from columns in csv and running sparql query type for each id
        df_path = pd.read_csv(args["path"])
        if df_path.shape[0] == 0:
            raise ValueError(("csv should not be empty"))

        ids = df_path[args["column"]]
        if ids[0].startswith("http"):
            ids = [x.split("/")[-1] for x in ids]

        df_output = None

        for curr_id in ids:
            curr_df = get_output_sparql(query=SPARQL_QUERIES[args['query_type']](curr_id))
            if isinstance(curr_df, pd.DataFrame):
                df_output = pd.concat([df_output, curr_df]) \
                    if isinstance(df_output, pd.DataFrame) else curr_df

        if args["save_path"]:
            df_output.to_csv(args["save_path"])

    return df_output


if __name__ == '__main__':
    """
    Q6534: French Revolution
    Q142: France
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("-id", '--id', default=None,
                    help="id of node to extract info from")
    ap.add_argument("-p", "--path", default=None,
                    help="csv path to extract query from. " + \
                        "Ids will be taken in the column given in argument")
    ap.add_argument("-col", "--column", default=None,
                    help="if csv path given, column to extract the ids from")
    ap.add_argument("-q", '--query_type', required=True,
                    help="type of query to execute, check SPARQL_QUERIES")
    ap.add_argument("-c", '--clean_df', default=1,
                    help="whether to clean or not the sparqlwrapper output")
    ap.add_argument("-s", '--save_path', default=None,
                    help="if not None, path to store the df to, must be a .csv file")
    ARGS = vars(ap.parse_args())

    check_args(args=ARGS)
    main(ARGS)
