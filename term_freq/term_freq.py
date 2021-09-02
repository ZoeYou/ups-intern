#!/usr/bin/env python
import os
import re
import spacy

import argparse
from wasabi import msg
from tqdm import tqdm
from pathlib import Path
from random import sample
from collections import defaultdict


def extract_terms(list_terms, ner_doc, span_doc):
    res = set()
    #ner_doc = ner(patent)
    #span_doc = span(patent)

    ents = [ent for ent in ner_doc.ents if ent.label_ == 'TERM']
    spans = [span for span in span_doc.spans['grit']]
    for term in ents + spans:
        term_text = term.text       
        try:
            match = re.search('(\(|(\.|;)\\n|\\n|(\.|;) |;\\n- |(\.|;)\\n)[a-zA-Z0-9_]*', term_text)
            while match:
                term_text = term_text[:match.start()]
                match = re.search('(\(|(\.|;)\\n|\\n|(\.|;) |;\\n- |(\.|;)\\n)[a-zA-Z0-9_]*', term_text)
                if term_text.isdigit(): continue
                 
                while (term_text[-1] in ['.','_', ';', '\n', ' ', ',', '=']) and (not term_text.isupper() or (term_text.isupper() and len(term_text)<=3)):
                    term_text = term_text[:-1]
                if term_text.isdigit(): continue

                while  (term_text[0] in ['.','_', ';', '\n', ' ', ',', '=']) and (not term_text.isupper() or (term_text.isupper() and len(term_text)<=3)):
                    term_text = term_text[1:]
                if term_text.isdigit(): continue

        except IndexError: # single character
            continue

        if term_text not in list_terms:
            res.add(term_text)
    return res
        



def main():
    parser = argparse.ArgumentParser()

    ## Required parameters
    parser.add_argument("--in_file",
                        default=None,
                        type=str,
                        required=True,
                        help="Path to input patents file.")

    parser.add_argument("--out_dir",
                        default=None,
                        type=str,
                        required=True,
                        help="Path to output directory.")

    parser.add_argument("--model_ner",
                        default=None,
                        type=str,
                        required=True,
                        help="Path to the spaCy nlp model for ner.")

    parser.add_argument("--model_spanCat",
                        default=None,
                        type=str,
                        required=True,
                        help="Path to the spaCy nlp model for span categorizer")

  
    args = parser.parse_args()


    input_path = Path(args.in_file)
    output_path = Path(args.out_dir)
    if not input_path.exists():
        raise FileNotFoundError("Input file does not exist.")
    if not output_path.exists():
        output_path.mkdir(parents=True)
        msg.good(f"Created output directory {args.out_dir}")
    
    #files_list = list(input_path.rglob('*.txt'))
    output_file = output_path / f"{input_path.stem}_2015.txt"


    all_terms = set()
    ner = spacy.load(args.model_ner)
    spanCat = spacy.load(args.model_spanCat, disable=['tagger','parser','ner','lemmatizer','textcat'])

    #ner.max_length = 1500000
    #spanCat.max_length = 1500000

    
    #for file in tqdm(files_list[:]):
    msg.text(f"Preprocessing text of {args.in_file}...")
        # retrieve all patents in the file
    with open(args.in_file, 'r') as f:
        lines = [] 
        for line in tqdm(f):
            if '____' not in line: lines.append(line)
        #lines = f.read().splitlines()
        #patents = '\n'.join([line for line in lines if '____' not in line])
  
        #patents = [''.join(lines[x:x+1000]) for x in range(0, len(lines), 1000)]
        patents = ''.join(lines).split('\n\n\n')
        print('joined: ', len(patents))
    
    ner_docs = ner.pipe(patents, n_process=4)
    span_docs = spanCat.pipe(patents, n_process=4)

    #for patent in tqdm(patents):
    for ner_doc, span_doc in tqdm(zip(ner_docs, span_docs)):
        temp_res = extract_terms(all_terms, ner_doc, span_doc)
        print(temp_res)
        all_terms.update(temp_res)
  
  
    with output_file.open('w', encoding='utf8') as f:
        for line in all_terms:
            f.write(line.strip(' .') + '\n')
    msg.good(f"Complete. Concatenated {len(all_terms)} patents to file {output_file.resolve()}")
    

if __name__ == "__main__":
    main()
