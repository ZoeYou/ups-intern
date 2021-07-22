#!/usr/bin/env python3

"""Get Wikidata dump records as a JSON stream (one JSON object per line)"""
# Modified script taken from this link: "https://www.reddit.com/r/LanguageTechnology/comments/7wc2oi/does_anyone_know_a_good_python_library_code/dtzsh2j/"

import bz2
import json
import pandas as pd
import pydash

i = 0
# an empty dataframe which will save items information
# you need to modify the columns in this data frame to save your modified data
# TODO
df_record_all = pd.DataFrame(columns=['entity_id', 'entity_name','aliases', 'property', 'value_id', 'description'])

def wikidata(filename):
    with bz2.open(filename, mode='rt') as f:
        f.read(2) # skip first two bytes: "{\n"
        for line in f:
            try:
                yield json.loads(line.rstrip(',\n'))
            except json.decoder.JSONDecodeError:
                continue

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
    'dumpfile',
    help=(
        'a Wikidata dumpfile from: '
        'https://dumps.wikimedia.org/wikidatawiki/entities/'
        'latest-all.json.bz2'
        )
    )
    args = parser.parse_args()
    for record in wikidata(args.dumpfile):
        ## only extract items with properties we need
        target_properties = {'P31': 'instance of',
                            'P279': 'subclass of',
                            'P361': 'part of',
                            'P366': 'use',
                            'P527': 'has part',
                            'P1269': 'facet of'}

        for prop in target_properties.keys():
            if pydash.has(record, f'claims.{prop}'):
            #and pydash.get(record, f'claims.{prop}.mainsnak.datatype') == 'wikibase-item':

                print('i = '+str(i)+' item '+record['id']+'  started!')       
                #print(pydash.get(record, f'claims.{prop}'))

                item_id = pydash.get(record, 'id')
                english_label = pydash.get(record, 'labels.en.value')
                aliases = pydash.get(record, 'aliases.en.value')
                english_desc = pydash.get(record, 'descriptions.en.value')

                for dic in pydash.get(record, f'claims.{prop}'):
                    if pydash.get(dic, 'mainsnak.datatype') == 'wikibase-item':
                        value_id = pydash.get(dic, 'mainsnak.datavalue.value.id')
                        df_record = pd.DataFrame({'entity_id': item_id, 'entity_name': english_label, 'aliases': aliases, 'property': prop, 'value_id': value_id, 'description': english_desc}, index=[i])
                        df_record_all = df_record_all.append(df_record, ignore_index=True)

                        i += 1
                        print(i)
                        if (i % 5000 == 0):
                            pd.DataFrame.to_csv(df_record_all, path_or_buf='./wikidata/extracted/till_'+record['id']+'_item.csv')
                            print('i = '+str(i)+' item '+record['id']+'  Done!')
                            print('CSV exported')
                            df_record_all = pd.DataFrame(columns=['entity_id', 'entity_name','aliases', 'property', 'value_id', 'description'])

                     
    pd.DataFrame.to_csv(df_record_all, path_or_buf='./wikidata/extracted/final_csv_till_'+record['id']+'_item.csv')
    print('i = '+str(i)+' item '+record['id']+'  Done!')
    print('All items finished, final CSV exported!')
