#!/usr/bin/env python
import json
import argparse
import pandas as pd 
import numpy as np
from wasabi import msg
from tqdm import tqdm


def term2jsonl(term, case_sensitive, label = 'TERM'): 
    json_line = {}
    json_line["label"] = label 

    if case_sensitive:
        json_line["pattern"] = term 
    else:
        json_line["pattern"] = [{"lower":token} for token in term.lower().split()] 
    
    return json.dumps(json_line)


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

    parser.add_argument("--case_sensitive",
                        default=True,
                        type=str,
                        help="Whether the pattern should be case insensitive, True as default.")

    args = parser.parse_args()

    msg.text("Uploading data...")
    matching_list = pd.read_csv(args.terms_file, delimiter='\t', dtype={'wiki_title': str})

    msg.text("Start creating patterns:")
    with open(args.out_dir+'patterns.jsonl','w') as f:
        terms = np.concatenate((matching_list.term.values.astype(str), matching_list.wiki_title.values.astype(str)))
        terms = set(terms)  # remove the duplicate
        for term in tqdm(terms):
            f.write(term2jsonl(term, args.case_sensitive) + '\n')
    msg.good(
        f"Completed. Saved final {len(terms)} patterns to file."
    )


if __name__ == "__main__":
    main()