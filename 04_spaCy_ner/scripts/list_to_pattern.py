#!/usr/bin/env python
import json
import argparse
import pandas as pd 
from wasabi import msg
from tqdm import tqdm


def term2jsonl(term, case_insensitive, label = 'TERM'):
    tokens = term.lower().split()
    
    json_line = {}
    json_line["label"] = label 

    if case_insensitive:
        json_line["pattern"] = [{"lower":token} for token in tokens]  
    else:
        json_line["pattern"] = [token for token in tokens]
    
    return json.dumps(json_line).replace(" ","")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--terms_file",
                        default=None,
                        type=str,
                        required=True,
                        help="The .csv file used to create the new pattern jsonl.")
    
    parser.add_argument("--out_dir",
                        default=None,
                        type=str,
                        required=True,
                        help="Path to output directory.")

    parser.add_argument("--case_insensitive",
                        default=True,
                        type=str,
                        help="Whether the pattern should be case insensitive, True as default.")

    args = parser.parse_args()

    msg.text("Uploading data...")
    matching_list = pd.read_csv(args.terms_file, delimiter='\t', dtype={'wiki_title': str})

    msg.text("Start creating patterns:")
    with open('patterns.jsonl','w') as f:
        terms = matching_list.term.values.astype(str)
        for term in tqdm(terms):
            f.write(term2jsonl(term, args.case_insensitive) + '\n')
    msg.good(
        f"Completed. Saved final {len(matching_list)} patterns to file."
    )


if __name__ == "__main__":
    main()