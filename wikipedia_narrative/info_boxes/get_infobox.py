# -*- coding: utf-8 -*-
""" Retrieving info from infoboxes """
import re
import wptools
import streamlit as st
import urllib3
import requests
from bs4 import BeautifulSoup
from wikipedia_narrative.info_boxes.pre_process_infobox import \
    filter_infobox_edges, merge_infobox_edges


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_html_from_url(url: str) -> BeautifulSoup:
    """ Retrieving html from url """
    session = requests.Session()
    html = session.get(url, verify=False).content
    return BeautifulSoup(html, 'lxml')


def extract_infobox_no_url(page_name:str, options:list[str] = []) -> dict:
    """ Extract infobox with wptools module from page_name
    Possible options are:
    1. Keeping only specific labels in infoboxes
    2. Merging similar labels (i.e. one representative class for several edges)
    3. Pre-processing content of infoboxes values (for later narrative building) """
    page = wptools.page(page_name, show=False)
    page.get_parse()
    if page.data['infobox']:
        infobox = page.data['infobox']
        if "1" in options:  # Only keep relevant infobox labels for the narrative
            infobox = filter_infobox_edges(infobox=infobox)
        if "2" in options:  # Merge similar infobox labels
            infobox = merge_infobox_edges(infobox=infobox)

        infobox = {k: {"text": val} for k, val in infobox.items()}

        return infobox
    return dict()


def get_link_from_html(html_content: BeautifulSoup) -> dict[str, str]:
    """ Retrieving href links found in infobox
    Output format = dict[<text pointing to link>, <url of link>] """
    output = html_content.find('table', {'class': 'infobox'})

    if not output:
        return dict()

    return {x.text.strip(): x.get('href', '') for  x in output.find_all('a')}


img_noise = ["Question_book-new.svg", 'Translation_to_english_arrow.svg',
             'Text_document_with_page_number_icon.svg', 'Text_document_with_red_question_mark.svg',
             'Ambox_important.svg']

def get_img_src(html_content: BeautifulSoup) -> str:
    """ Returning url of first img find in html_content, exclusing noisy images """
    imgs = html_content.find_all("img")
    for img in imgs:
        if (img.get('alt', '') not in \
            ['This is a good article. Click here for more information.']) and \
            (all(elt not in img.get('src') for elt in img_noise) ):
            return img.get('src', '')
    return ''

@st.cache(show_spinner=False)
def add_url(infobox: dict, links: dict[str, str]) -> dict[str, dict]:
    """ For each infobox label in infobox:
    1. Detecting links (delimited by [[]])
    2. Adding corresponding href found in infobox """
    res = dict()
    for pred, val in infobox.items():
        if isinstance(type(val["text"]), str):
            urls = list()
            cand_links = re.findall(pattern="\\[\\[([^\\[]+)\\]\\]+?", string=val["text"])
            for cands in cand_links:
                for cand in cands.split("|"):
                    try:
                        urls.append(f"https://en.wikipedia.org{links[cand.strip()]}")
                    except Exception as error:
                        print(error)
            val.update(dict(href=urls))
            res[pred] = val
        else:
            val.update(dict(href=list()))
            res[pred] = val
    return res


if __name__ == '__main__':
    INFOBOX = extract_infobox_no_url(page_name='Coup of 18 Fructidor', options=["1", '2', '3'])
    HTML_CONTENT = get_html_from_url(url="https://en.wikipedia.org/wiki/Coup_of_18_Fructidor")
    LINKS = get_link_from_html(html_content=HTML_CONTENT)
    RES = add_url(INFOBOX, LINKS)
    print(RES)
