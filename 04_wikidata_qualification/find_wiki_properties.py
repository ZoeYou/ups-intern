#!/usr/bin/env python
import argparse
import spacy 
import json
import requests 
import urllib
import re
import wikipedia
import numpy as np
import pandas as pd

from wasabi import msg
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')


target_properties = {'P31': 'instance of',
                     'P279': 'subclass of',
                     'P361': 'part of',
                     'P366': 'use',
                     'P527': 'has part',
                     'P1269': 'facet of'
                    }

def find_wiki_title(term):
    title = wikipedia.search(term)
    if title:
        return title[0]
    
def find_wiki_summary(term):
    try:
        return wikipedia.summary(term)
    # if it is a ambiguous term, the function will return None as value of summary
    except wikipedia.exceptions.WikipediaException:
        return None    
    
def get_wikidata_id(term):  
    encoded_term = urllib.parse.quote(term)

    url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&ppprop=wikibase_item&redirects=1&titles={encoded_term}"
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser').get_text()
    
    wikidata_id = re.findall('wikibase_item\"\:\"(.*)?\".*', soup)
    
    if wikidata_id != []:
        return wikidata_id[0]    
    
def not_disambiguation_page(wikidata_id):
    url = "https://www.wikidata.org/wiki/" + wikidata_id
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')
    
    div = soup.find("div", {"class": "wikibase-entitytermsview-heading-description"}).text
    
    return div != 'Wikimedia disambiguation page'


def retrieve_value_P(P):
    return target_properties[P]


def retrieve_value_Q(Q):    
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=labels&languages=en&ids={Q}"
    json_response = requests.get(url).json()
    entities = json_response.get('entities')
    
    entity = entities.get(Q)
    if entity:
        labels = entity.get('labels')
        if labels:
            en = labels.get('en')
            if en:
                value = en.get('value')
                return value 


def get_target_ItemProperties(wikidata_item, wikidata_id):
    url = "https://www.wikidata.org/w/api.php?action=wbgetclaims&format=json&entity="+wikidata_id
    json_response = requests.get(url).json()

    properties = [*json_response.get('claims').values()]
    
    res = np.empty(shape=[0, 3])
    
    for p in properties:   
        for d in p: 
            dict_ = d['mainsnak']
        
            # ignore if not a wikibase item or not in target properties
            if dict_['datatype'] != 'wikibase-item' or dict_['snaktype'] != 'value' or dict_['property'] not in target_properties:
                continue 
                
            # replace all the wikidataItem ID by wikidataItem name          
            property_value = retrieve_value_Q(dict_['datavalue']['value']['id'])
            
            if property_value is None:
                continue
            
            # find property value in the previous lookup table
            property_ = retrieve_value_P(dict_['property'])         
            row_to_append = [wikidata_item, property_, property_value]  
            res = np.append(res, [row_to_append], 0)  
  
    return res 

    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_file",
                        default=None,
                        type=str,
                        required=True,
                        help="Path of the patent text file after being preprocessed.")
    
    parser.add_argument("--out_dir",
                        default=None,
                        required=True,
                        type=str,
                        help="Path to output directory.")

    parser.add_argument("--spacy_model",
                        default=None,
                        required=True,
                        type=str,
                        help="Path to the spaCy ner model.")

    parser.add_argument("--wikidata_id",
                        default='./wikidata_id.json',
                        type=str,
                        help="Path to wikidata id lookup table.")
    
    parser.add_argument("--wikidata_property",
                        default='./wikidata_properties.txt',
                        type=str,
                        help="Path to wikidata properties already have.")
    
    parser.add_argument("--title_summary",
                        default='../01_make_matching_list/title_summary.json',
                        type=str,
                        help="Path to wikipedia information with title and summary.")

    args = parser.parse_args()
    

    
    # load input/ output file
    input_path = Path(args.in_file)
    output_path = Path(args.out_dir)
    
    if not input_path.exists():
        msg.fail("Can't find input file", in_file, exits=1)   
    else:
        with input_path.open("r", encoding="utf8") as f:
            patents = f.read().split('\n\n\n')       
    
    if not output_path.exists():
        output_path.mkdir(parents=True)
        msg.good(f"Created output directory {output_path}")
    
    # load spaCy model
    nlp = spacy.load(args.spacy_model)
    msg.info(f"Using spaCy model {args.spacy_model}")  
   
    # load wikidata_id file and wikidata_property file
    msg.text("Loading wikidata id lookup table...")
    with open(args.wikidata_id, 'r', encoding='utf-8') as f:
        DICT_WIKIDATA_ID = json.load(f)
    msg.text("Loading wikidata property file...")
    #wikidata_property = np.loadtxt(args.wikidata_property, delimiter='\t', dtype='str')
    wikidata_property = pd.read_csv(args.wikidata_property, delimiter='\t', header=None)
    
    # read json file of wikipedia page title and summary
    with open(args.title_summary, 'r', encoding='utf-8') as f:
        DICT_PAGE_TITLE = json.load(f)

    def ner2wiki(text, nlp, wikidata_property): # find entities and complete its wiki information (wiki title, summary, wikidata id and properties)                                                             
        doc = nlp(text)
        for ent in tqdm(doc.ents):
            term = ent.text
            try:
                wiki_title = DICT_PAGE_TITLE[term]['title']
            except KeyError:
                wiki_title = find_wiki_title(term)  
                if wiki_title:
                    wiki_summary = find_wiki_summary(wiki_title)
                    DICT_PAGE_TITLE.update({term:{'title':wiki_title, 'summary': wiki_summary}})
                else:
                    DICT_PAGE_TITLE.update({term:{'title': None, 'summary': None}})
                
            # find wikidata id and properties
            if wiki_title and wiki_title not in DICT_WIKIDATA_ID:
                wikidata_id = get_wikidata_id(wiki_title)
                if wikidata_id and not_disambiguation_page(wikidata_id):
                    DICT_WIKIDATA_ID.update({wiki_title: wikidata_id})
                    # find wiki properties 
                    list_to_append = get_target_ItemProperties(wiki_title, wikidata_id)
                    #wikidata_property = np.vstack((wikidata_property, list_to_append))
                    wikidata_property = wikidata_property.append(pd.DataFrame(list_to_append, columns=wikidata_property.columns), ignore_index=True)
        return wikidata_property   

    msg.text('Extracting wiki information for entities in patent file:')
    for patent in patents[0]:
        properties_found = ner2wiki(patent, nlp, wikidata_property)    
        #wikidata_property = np.vstack((wikidata_property, properties_found))
        wikidata_property = wikidata_property.append(pd.DataFrame(properties_found, columns=wikidata_property.columns), ignore_index=True)
        
    # save the update files
    with open(args.wikidata_id, "w", encoding='utf-8') as f: 
        json.dump(DICT_WIKIDATA_ID, f, indent = 4)
    #np.savetxt(args.wikidata_property, wikidata_property, delimiter='\t', fmt='%s', dtype='str')
    wikidata_property.to_csv (args.wikidata_property, index = False, header=None, sep='\t')
    
    with open(args.title_summary, "w", encoding='utf-8') as f: 
        json.dump(DICT_PAGE_TITLE, f, indent = 4)
        
        
if __name__ == "__main__":
    main()  
    

    
    
    
    
    
    
