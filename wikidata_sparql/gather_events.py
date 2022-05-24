""" Collect events """
import argparse
import pandas as pd
import streamlit as st
import wikidata_sparql.sparql_query as sparql_query

ARGS = [
    {"id": "Q6534", "query_type": "obj-part-of-id",
        "path": None, "column": None, "clean_df": 1, "save_path": None},
    {"id": "Q142", "query_type": "obj-instance-of-historical-country-and-has-country-id",
        "path": None, "column": None, "clean_df": 1, "save_path": None},
    {"id": "Q6534", "query_type": "id-has-significant-event-obj",
        "path": None, "column": None, "clean_df": 1, "save_path": None}
]


ARGS_PROPERTY = {"id": None, "query_type": "forward_links",
                 "path": "unique_events_demo.csv", "column": "event",
                 "clean_df": 1, "save_path": "unique_events_forward_links.csv"}


def build_args_for_collect(id_query_type_l: list[tuple[str, str, str, str]]) -> list[dict]:
    """
    Args:
        - id_query_type_l:
            Each tuple has the format
            (<Wikidata ID>, <query_type>, year_begin, year_end)
            to prepare arguments to retrieve data from Wikidata
            <Wikidata ID> is the starting point to retrieve data from wikidata,
            <query_type> specifies the key to the SPARQL query to be run.
            query_type should be a key in SPARQL_QUERIES in the ./query_db.py script
    Returns:
        - list of arguments to call the sparql_query.py script
    """
    res = list()
    for (curr_id, query_type, y_b, y_e) in id_query_type_l:
        if query_type == "obj-instance-of-historical-country-and-has-country-id":
            res.append({"id": {"id": curr_id, "year_begin": y_b, "year_end": y_e},
                        "query_type": query_type, "path": None,
                        "column": None, "clean_df": 1, "save_path": None})
        else:
            res.append({"id": curr_id, "query_type": query_type,
             "path": None, "column": None, "clean_df": 1, "save_path": None})
    return res


@st.cache(show_spinner=False)
def collect_data(args_collect_list: list[dict] = ARGS) -> pd.core.frame.DataFrame:
    """
    Args:
        - args_collect_list
            List of arguments to extract Wikidata content.
            Cf. ARGS above example for further specifications
    Returns:
        - DataFrame containing all instances found
            within wikidata with the SPARQL queries
    """
    df_concat = None

    # Running each sparql query given in input
    # Concatenate results in dataframe
    for arg in args_collect_list:
        curr_df = sparql_query.main(arg)
        if isinstance(curr_df, pd.DataFrame):
            df_concat = pd.concat([df_concat, curr_df]) \
                if isinstance(df_concat, pd.DataFrame) else curr_df

    return df_concat


def check_args(args: dict):
    """ Checking args in command line to execute script"""
    if args["type"] not in ["collect", "expand"]:
        raise ValueError("Please check helper documentation, " + \
            "`type` should be either `collect` or `expand`")

    if not args["save"].endswith('.csv'):
        raise ValueError("`save` should be a .csv file")

    if (args["type"] == "expand") and (not args["path"]):
        raise ValueError("If type is `expand`, both `path` and `column` arg should be specified")


if __name__ == '__main__':
    """ To be executed in shell from `wikidata_sparql` folder
    To first collect the events and then retrieve the outgoing links,
    below are examples of scripts to execute:
    - python gather_events.py -t collect \
        -s ../data/events_demo.csv
    - python gather_events.py -t expand \
        -s ../data/unique_events_forward_links.csv \
            -p ../data/events_demo.csv """
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", '--type', required=True,
                    help="Type of objects to retrieve from wikidata." +
                         "`collect` to retrieve original events - " + \
                             "e.g. <e> part of <French Revolution>" + \
                         "`expand` to retrieve outgoing links from events")
    ap.add_argument("-s", "--save", required=True,
                    help="csv save path for the output of the script")
    ap.add_argument("-p", "--path", default=None,
                    help="csv path to extract query from if type is `expand`. " + \
                        "Ids will be taken in the column given in argument")
    ap.add_argument("-c", "--column", default="event",
                    help="if args `path` given, column to extract the ids from")
    ARGS = vars(ap.parse_args())

    check_args(args=ARGS)

    if ARGS["type"] == "collect":

        DF_CONCAT = collect_data()
        DF_CONCAT.to_csv(ARGS["save"])
        DF_CONCAT.drop_duplicates().to_csv(
            f"{'/'.join(ARGS['save'].split('/')[:-1])}" + \
                f"/unique_{ARGS['save'].split('/')[-1]}")

    else:  # args["type"] == "expand"
        ARGS_PROPERTY.update(
            {"save_path": ARGS["save"],"path": ARGS["path"],
            "column": ARGS["column"]})
        sparql_query.main(ARGS_PROPERTY)
