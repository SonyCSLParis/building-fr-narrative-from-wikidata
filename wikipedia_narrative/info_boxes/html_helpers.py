# -*- coding: utf-8 -*-
""" Html helpers for infoboxes """
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_html_from_url(url: str) -> BeautifulSoup:
    """ Retrieving html from url """
    session = requests.Session()
    html = session.get(url, verify=False).content
    return BeautifulSoup(html, 'lxml')


def get_wp_url_from_wd_id(wikidata_id:str, lang:str = 'en', debug:bool = False) -> str:
    """ Retrieving Wikipedia URL from Wikidata page. If not found return empty string """

    url = "https://www.wikidata.org/w/api.php?action=wbgetentities&props=sitelinks/" + \
        f"urls&ids={wikidata_id}&format=json"
    json_response = requests.get(url).json()
    if debug:
        print(wikidata_id, url, json_response)

    try:
        url = json_response.get('entities').get(wikidata_id) \
            .get('sitelinks').get(f'{lang}wiki').get('url')
        return requests.utils.unquote(url)

    except Exception as error:
        print(error)
        return ""
