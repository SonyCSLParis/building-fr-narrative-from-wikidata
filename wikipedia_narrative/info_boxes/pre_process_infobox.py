# -*- coding: utf-8 -*-
""" Pre processing info boxes labels """
import os
import re
import yaml
from settings.settings import ROOT_PATH

with open(os.path.join(ROOT_PATH, "wikipedia_narrative/info_boxes/to_discard.txt"), 'r') as file:
    to_discard_patterns = [elt.strip() for elt in file.read().split("\n")]

with open(os.path.join(ROOT_PATH, "wikipedia_narrative/info_boxes/merge_labels.yaml"), 'r') as file:
    merge_labels = yaml.load(file, Loader=yaml.FullLoader)

LABEL_TO_REPR = {k: v for v, l in merge_labels.items() for k in l}


def filter_infobox_edges(infobox: dict,
                         to_filter: list[str] = to_discard_patterns) -> dict[str, str]:
    """ Return only keys and values that are not in to_filter """
    return {k: v for k, v in infobox.items() if \
        not any(re.search(pattern, k) for pattern in to_filter)}


def merge_infobox_edges(infobox:dict,
                        label_to_repr: dict[str, str] = LABEL_TO_REPR) -> dict[str, str]:
    """ Merging labels that are similar with one representant only """

    # Special cases
    if "year_start" and "date_start" in infobox:
        infobox["date_start"] = f"{infobox['date_start']} {infobox['year_start']}"
        del infobox["year_start"]
    if "year_end" and "date_end" in infobox:
        infobox["date_end"] = f"{infobox['date_end']} {infobox['year_end']}"
        del infobox["year_end"]

    # Merging labels that are similar
    new_infobox = dict()
    for label, _ in infobox.items():
        if label[-1].isdigit() and label[:-1] in label_to_repr:
            digit = label[-1]
            new_infobox[f"{label_to_repr[label[:-1]]}{digit}"] = infobox[f"{label[:-1]}{digit}"]
        elif label in label_to_repr:
            new_infobox[label_to_repr[label]] = infobox[label]
        else:
            new_infobox[label] = infobox[label]

    return new_infobox
