#!/usr/bin/env python
import json
import spacy 
import re 
import argparse
import random 
import os
from wasabi import msg
from tqdm import tqdm
from spacy.tokens import DocBin


def create_patterns(patterns_file):
    with open(patterns_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    json_lines = [json.loads(line) for line in lines]
    return json_lines

# def save_data(dataset, eval_size, out_file):
#     random.shuffle(dataset)
#     split = int(len(dataset) * eval_size)

#     TRAIN_DATA = dataset[split:]
#     TEST_DATA = dataset[:split]
#     with open(out_file, 'w', encoding='utf-8') as f:
#         json.dump(TRAIN_DATA, f, indent=4)

def convert_format(dataset):
    nlp = spacy.blank('en')
    db = DocBin()

    for text, ann in tqdm(dataset):
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in ann['entities']:
            span = doc.char_span(start, end, label=label, alignment_mode = 'contract')
            if span != None:
                ents.append(span)
        doc.ents = ents 
        db.add(doc)
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
                        default=None,
                        type=str,
                        required=True,
                        help="Path to output directory.")

    parser.add_argument("--patterns_file",
                        default='./assets/patterns.jsonl',
                        type=str,
                        help="Path of the patterns file.")

    parser.add_argument("--eval_size",
                        default=0.2,
                        type=float,
                        help="Split rate of evaluation dataset.")

    # parser.add_argument("--max_docs",
    #                     default=10 ** 6,
    #                     type=int,
    #                     help="Maximum docs per batch."           
    # )

    args = parser.parse_args()


    # read patterns
    msg.text("Reading pattern file...")

    patterns = create_patterns(patterns_file = args.patterns_file)
    msg.good(f"Read {len(patterns)} pattern rules.")

    # create spacy entity ruler
    msg.text("Creating entity ruler...")
    nlp = spacy.blank("en")
    ruler = nlp.add_pipe("entity_ruler")
    ruler.add_patterns(patterns)
    msg.good("Complete.")

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
    for sentence in tqdm(sentences[:10000]):
        doc = nlp(sentence)
        entities = []    
        for ent in doc.ents:
            entities.append([ent.start_char, ent.end_char, ent.label_])
        DATA.append([sentence, {"entities": entities}])    

    # split to training and evaluation set
    TRAIN_DATA, TEST_DATA = train_eval_split(dataset = DATA, eval_size = args.eval_size)
     

    # transform data format from jsonl to spacy v3.0's version .spacy
    msg.text('Converting data format from jsonl to .spacy format:')

    db_train = convert_format(dataset=TRAIN_DATA)
    db_eval = convert_format(dataset=TEST_DATA)

    # save .spacy file
    patent_name = os.path.basename(args.in_file).split('_')[0]
    db_train.to_disk(f"{args.out_dir}/{patent_name}_terms_training.spacy")
    db_eval.to_disk(f"{args.out_dir}/{patent_name}_terms_eval.spacy")
    msg.good(f"Processed totally {len(db_train) + len(db_eval)} documents to {args.out_dir}")



if __name__ == "__main__":
    main()
