#!/usr/bin/env python
import json
import spacy 
import re 
import argparse
import random 
import os
import pandas as pd

from wasabi import msg
from pathlib import Path
from tqdm import tqdm

from spacy.tokens import DocBin, Span
from spacy.matcher import Matcher
from spacy.tokenizer import Tokenizer
from spacy.util import compile_infix_regex
from collections import defaultdict

def collect_sents(doc, matcher):
    """
    collect sentences with matched spans, 
    if overlapping then pick up the longest else pick up the 1st
    """
    matches = matcher(doc)
    dict_sents = defaultdict(list)
    
    spans = [Span(doc, start, end, label=match_id) for match_id, start, end in matches]
    #for span in spacy.util.filter_spans(spans): 
    for span in spans:
        term = doc[span.start: span.end]      
        sent = term.sent  # Sentence containing matched span
    # Append mock entity for match in displaCy style to matched_sents
    # get the match span by ofsetting the start and end of the span with the
    # start and end of the sentence in the doc
        try:
            term_text = term.text
            
            match = re.search('(\(|(\.|;)\\n|\\n|(\.|;) |;\\n- |(\.|;)\\n)[a-zA-Z0-9_]*', term_text)
            while match:
                term.end_char = term.start_char + match.start()
                term_text = term_text[:match.start()]
                match = re.search('(\(|(\.|;)\\n|\\n|(\.|;) |;\\n- |(\.|;)\\n)[a-zA-Z0-9_]*', term_text)
            if term_text.isdigit(): continue
                               
            while term_text[-1] in ['.','_','\n',';',',',' ','>','/','<','='] and (not term_text.isupper() or (term_text.isupper() and len(term_text)<=3)):
                term.end_char -= 1
                term_text = term_text[:-1]

            while term_text[0] in ['.','_','\n',';',',',' ','>','/','<','='] and (not term_text.isupper() or (term_text.isupper() and len(term_text)<=3)):
                term.start_char += 1
                term_text = term_text[1:]

            if term_text.isdigit(): continue

        except IndexError: # single character
            continue
            
        match_ents = (
            term.start_char - sent.start_char,  # start
            term.end_char - sent.start_char,    # end 
            "TERM", # label
        )
        dict_sents[sent.text].append(match_ents)

    dict_sents = dict(dict_sents)
    return [(key, {"entities": value}) for key, value in dict_sents.items()]


def save_data(dataset, out_file):
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=4)


def convert_format(dataset, span_key):
    nlp = spacy.blank('en')
    db = DocBin()

    for text, ann in tqdm(dataset):
        try:
            doc = nlp.make_doc(text)
            spans = []
            for start, end, label in ann['entities']:
                span = doc.char_span(start, end, label=label, alignment_mode = 'contract')
                if span != None:
                    spans.append(span)
            doc.spans[span_key] = spans 
            db.add(doc)
        except ValueError:
            continue
    return db

def train_eval_split(dataset, eval_size):
    random.shuffle(dataset)
    split = int(len(dataset) * eval_size)

    train_data = dataset[split:]
    eval_data = dataset[:split]
    return (train_data, eval_data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_file",
                        default=None,
                        type=str,
                        required=True,
                        help="Path of the patent text file after being preprocessed.")
    
    parser.add_argument("--out_dir",
                        default='./corpus',
                        type=str,
                        help="Path to output directory.")

    parser.add_argument("--matching_list",
                        default='../01_make_matching_list/matching_list.csv',
                        type=str,
                        help="Path of the matching list file.")

    parser.add_argument("--eval_size",
                        default=0.1,
                        type=float,
                        help="Split rate of evaluation dataset.")

    parser.add_argument("--max_docs",
                        default=50000,
                        type=int,
                        help="Maximum docs per batch.")

    parser.add_argument("--span_key",
                        default='grit',
                        type=str,
                        help="span categorizer spans key"
                        )
           

    args = parser.parse_args()

    output_path = Path(args.out_dir)
    if not output_path.exists():
        output_path.mkdir(parents=True)
        msg.good(f"Created output directory {args.out_dir}")

    # create matcher
    msg.text("Creating Rule-based Matcher...")

    # load matching list
    term_list = pd.read_csv(args.matching_list, delimiter='\t', na_filter= False)

    # ==============================================PATTERNS_DEFINITION=================================================
    spacy.prefer_gpu()
    nlp = spacy.load("en_core_web_lg", disable=[ "ner", "lemmatizer", "textcat"])
    
    # remove "-" as spliter in tokenizer
    def custom_tokenizer(nlp):
        inf = list(nlp.Defaults.infixes)               # Default infixes
        inf.remove(r"(?<=[0-9])[+\-\*^](?=[0-9-])")    # Remove the generic op between numbers or between a number and a -
        inf = tuple(inf)                               # Convert inf to tuple
        infixes = inf + tuple([r"(?<=[0-9])[+*^](?=[0-9-])", r"(?<=[0-9])-(?=-)"])  # Add the removed rule after subtracting (?<=[0-9])-(?=[0-9]) pattern
        infixes = [x for x in infixes if '-|–|—|--|---|——|~' not in x] # Remove - between letters rule
        infix_re = compile_infix_regex(infixes)

        return Tokenizer(nlp.vocab, prefix_search=nlp.tokenizer.prefix_search,
                                    suffix_search=nlp.tokenizer.suffix_search,
                                    infix_finditer=infix_re.finditer,
                                    token_match=nlp.tokenizer.token_match,
                                    rules=nlp.Defaults.tokenizer_exceptions)

    nlp.tokenizer = custom_tokenizer(nlp)

    # add custom stop words 
    nlp.Defaults.stop_words |= {'K',
                             'absolutely',
                             'advantageous',
                             'all',
                             'always',
                             'appropriate',
                             'chief',
                             'classic',
                             'clear',
                             'common',
                             'concise',
                             'considerable',
                             'convenient',
                             'correct',
                             'critical',
                             'desirable',
                             'different',
                             'difficult',
                             'essential',
                             'ever',
                             'every',
                             'exact',
                             'example',
                             'exclusive',
                             'expected',
                             'few',
                             'fewer',
                             'forth',
                             'fourth',
                             'frequent',
                             'full',
                             'fundamental',
                             'general',
                             'important',
                             'key',
                             'laborious',
                             'less',
                             'limited',
                             'main',
                             'majority',
                             'mandatory',
                             'more',
                             'most',
                             'must',
                             'necessary',
                             'needed',
                             'new',
                             'none',
                             'old',
                             'only',
                             'partly',
                             'peculiar',
                             'permanent',
                             'poor',
                             'preferable',
                             'primary',
                             'principal',
                             'rare',
                             'required',
                             'said',
                             'second',
                             'secondary',
                             'significant',
                             'solely',
                             'special',
                             'such',
                             'superior',
                             'third',
                             'traditional',
                             'typical',
                             'uncommon',
                             'useful',
                             'usual',
                             'vital',
                             'present',
                             'corresponding',
                             'i-th',
                             'particular',
                             'fifth',
                             'sixth',
                             'plural',
                             'available',
                             'received',
                             'transmitted',
                             'yet',
                             'above-mentioned',
                             'FIELD',
                             'BACKGROUND',
                             'actual',
                             'comprising',
			                 'successful',
			                 'smaller',
			                 'large'
			                }

    # build matcher
    matcher = Matcher(nlp.vocab, validate=True)

    # build patterns
    patterns = []
    for term in tqdm(term_list.term.values):
        term_split = term.split(' ')
        if len(term_split) > 1: # if it is MWE
            patterns.append([{"POS": {"IN":["ADJ", "NOUN", "PROPN"]}, "OP": "*", "IS_STOP": False}] 
                            + [{"TEXT": token} for token in term_split]
                            + [{"POS": {"IN":["PROPN", "NOUN"]}, "OP": "*", "IS_STOP": False}])

        else: # if it is single word
            patterns.append([{"POS": {"IN":["ADJ", "NOUN", "PROPN"]}, "OP": "*", "IS_STOP": False}, 
                             {"TEXT": term_split[0], "POS": {"IN":["PROPN", "NOUN"]}},
                             {"POS": {"IN":["PROPN", "NOUN"]}, "OP": "*", "IS_STOP": False, "IS_DIGIT": False}])

            patterns.append([{"POS": {"IN":["ADJ", "NOUN", "PROPN"]}, "OP": "*", "IS_STOP": False},
                             {"TEXT": term_split[0], "POS": {"IN":["PROPN", "NOUN"]}},
                             {"TEXT": "of"},
                             {"POS": {"IN":["PROPN", "NOUN"]}, "OP": "+", "IS_STOP": False, "TEXT": {"NOT_IN": ["a"]}}])


    patterns.append([{"POS": {"IN":["PROPN", "NOUN"]}, "IS_TITLE": True, "OP": '+'}, 
                     {"POS": {"IN":["PROPN", "NOUN"]}, "IS_TITLE": True, "OP": '+'},
                     {"POS": {"IN":["PROPN", "NOUN"]}, "IS_TITLE": True, "OP": '+'}])     

    patterns.append([{"POS": {"IN":["PROPN", "NOUN"]}, 
                      "LENGTH": {"<=": 4}, 
                      "IS_STOP": False,
                      'TEXT': {'REGEX': '^[A-Z]{2,}[s]?', 
                               "NOT_IN": ["FIG", "FIGS", "CODE", "CORE", "TIME", "ART", "LIST"]}}])
    # ===================================================================================================================
    
    # add patterns to the matcher(this takes a quite long time)
    matcher.add('TERM', patterns) 
    msg.good(f"Added {len(patterns)} pattern rules.")

    # load patent data
    fig = re.compile(r'(figs?)\.',re.I) # FIG. ==> FIG
    patents = [fig.sub(r'\1',pat) for pat in open(args.in_file).read().split('\n\n\n')] # \1 represents the first group

    # split patents into sentences
    sentsplit = re.compile('[\n.;]')
    sentences = [li.strip() for pat in patents for li in sentsplit.split(pat) if len(li)>25 and '____' not in li]

    # create dataset
    msg.text("Creating NER dataset:")
    DATA = []

    #iterate over the sentences
    random.shuffle(sentences)
    for doc in tqdm(nlp.pipe(sentences[:args.max_docs], batch_size = 2000)):
        DATA.extend(collect_sents(doc, matcher))


    # split to training and evaluation set
    TRAIN_DATA, TEST_DATA = train_eval_split(dataset = DATA, eval_size = args.eval_size)  

    patent_name = os.path.basename(args.in_file).split('.')[0]
    ##save_data(TRAIN_DATA, f'{patent_name}_training.json')
    ##save_data(TEST_DATA, f'{patent_name}_eval.json')

    # transform data format from jsonl to spacy v3.0's version .spacy
    msg.text('Converting data format from jsonl to .spacy:')

    db_train = convert_format(dataset=TRAIN_DATA, span_key = args.span_key)
    db_eval = convert_format(dataset=TEST_DATA, span_key = args.span_key)

    # save .spacy file
    db_train.to_disk(f"{args.out_dir}/{patent_name}_training.spacy")
    db_eval.to_disk(f"{args.out_dir}/{patent_name}_eval.spacy")
    msg.good(f"Processed totally {len(TRAIN_DATA) + len(TEST_DATA)} documents to {args.out_dir}")



if __name__ == "__main__":
    main()
