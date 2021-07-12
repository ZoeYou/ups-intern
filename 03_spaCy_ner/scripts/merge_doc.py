#!/usr/bin/env python
import spacy
import os

from spacy.tokens import DocBin
from pathlib import Path
from wasabi import msg
from tqdm import trange


def main():
    target_path = Path('assets')
    training_list = list(target_path.rglob('*_2015_training.spacy'))
    eval_list = list(target_path.rglob('*_2015_eval.spacy'))
    assert len(training_list) == len(eval_list) and len(eval_list)>1
    msg.good(f'Read respectively {len(training_list)} datasets.')

    DocBin_training = DocBin().from_disk(training_list[0])
    DocBin_eval = DocBin().from_disk(eval_list[0])

    msg.text('Merging...')
    for i in trange(1,len(training_list)):
        DocBin_temp1 = DocBin().from_disk(training_list[i])
        DocBin_temp2 = DocBin().from_disk(eval_list[i])

        DocBin_training.merge(DocBin_temp1)
        DocBin_eval.merge(DocBin_temp2)

    msg.text('Saving files...')
    DocBin_training.to_disk('./assets/training_2015.spacy')
    DocBin_eval.to_disk('./assets/eval_2015.spacy')
    msg.good(f'Merged totally {len(DocBin_training)} training docs and {len(DocBin_eval)} evaluation docs to {target_path}')


if __name__ == "__main__":
    main()
