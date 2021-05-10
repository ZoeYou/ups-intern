#!/usr/bin/env python
import os
import re
import argparse
from wasabi import msg
from tqdm import tqdm
from pathlib import Path


def main():

    parser = argparse.ArgumentParser()

    ## Required parameters
    parser.add_argument("--in_dir",
                        default=None,
                        type=str,
                        required=True,
                        help="Path to input directory.")

    parser.add_argument("--out_dir",
                        default=None,
                        type=str,
                        required=True,
                        help="Path to output directory.")

    ## Other parameters
    parser.add_argument("--year",
                        default=2015,
                        type=int,
                        help="The earliest year to keep the patent files (inclusive), the patents before this year will not be retained.")
    
    parser.add_argument("--subclass",
                        default=None,
                        type=str,
                        help="subclass of target patents to retain eg. g06f")

    args = parser.parse_args()


    input_path = Path(args.in_dir)
    output_path = Path(args.out_dir)
    if not input_path.exists():
        raise FileNotFoundError("Input directory does not exist.")
    if not output_path.exists():
        output_path.mkdir(parents=True)
        msg.good(f"Created output directory {args.out_dir}")
    

    if args.subclass:
        files_list = list(input_path.rglob(f'{(args.subclass).upper()}*.txt'))
        output_file = output_path / f"{(args.subclass).upper()}_{args.year}.txt"
    else:
        files_list = list(input_path.glob('*.txt'))
        output_file = output_path / f"{input_path.parent.stem}{input_path.stem}_{args.year}.txt"

    with output_file.open('w', encoding='utf8') as f:
        cnt = 0
        msg.text("Preprocessing text...")
        for file in tqdm(files_list):
            # retrieve all patents in the file
            patents = [patent for patent in open(file).read().split('\n\n\n')]
            for patent in patents:

                patent_year = re.findall('\n_____(\d\d\d\d)\d', patent)
                if patent_year:
                    patent_year = int(patent_year[0])
                else:
                    continue

                # check patent released year
                if patent_year < args.year:
                    continue
                f.write(patent+'\n\n\n')
                cnt += 1

    msg.good(f"Complete. Concatenated {cnt} patents to file {output_file.resolve()}")
    

if __name__ == "__main__":
    main()