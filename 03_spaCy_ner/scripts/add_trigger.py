#!/usr/bin/env python
import spacy
import argparse
from wasabi import msg

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path",
                        default=None,
                        type=str,
                        required=True,
                        help="Path to the spaCy model")
    
    parser.add_argument("--trigger_list",
                        default='./wordsFVE.txt',
                        type=str,
                        help="Path to the trigger words list.")
           

    args = parser.parse_args()
    
    
    # load model
    nlp = spacy.load(args.model_path) 
    ruler = nlp.add_pipe("entity_ruler", config={"validate": True})
    
    # load trigger word list
    with open(args.trigger_list, encoding = 'utf-8', mode='r') as f:
        wordsFVE = f.read().replace('-','').strip()
    trigger_words = list(set([w for w in wordsFVE.split('\n') if w]))
 
    # create pattens of entity-ruler
    msg.text("Creating Rule-based Matcher...")
    
    rulers = [trigger for trigger in trigger_words]
    patterns = [{"label": "ERROR", "pattern": rule} for rule in rulers]
    ruler.add_patterns(patterns)
    msg.good(f"Added {len(patterns)} trigger words to the entity-ruler.")
    
    # resave the model with entity-ruler
    nlp.to_disk(args.model_path)   
    msg.good(f"Model resaved to {args.model_path}")



if __name__ == "__main__":
    main()
