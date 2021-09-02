import re
import pandas as pd
from tqdm import tqdm

# introduce wikidata
df = pd.read_csv('/mnt/beegfs/home/zuo/multidive/qatent-intern/04_wikidata_qualification/wikidata/wikidata_RDF.csv')
df_filtered = df[df.property != 'instance of']
terms = list(set(df_filtered.name1.values.tolist())) + list(set(df_filtered.name2.values.tolist()))

# filter year
pattern_year = re.compile('\d{4}')
terms = [term for term in terms if not pattern_year.search(term)] 
print('wikidata done!')
print(len(terms))

# introduce wikipedia category trees
with open('/mnt/beegfs/home/zuo/multidive/hh_pred/data/all_paths_lem.txt', 'r') as in_f:
    lines = in_f.read().splitlines()[:10]
    lines = [line.split(' ') for line in lines]
    terms_to_append = [term.replace('_',' ') for term in [j for sub in lines for j in sub]]
    print(terms_to_append)
print('wiki category trees done!')

terms = terms + terms_to_append
print(len(terms))

with open('wiki_terms.txt', 'w') as f:
    for t in terms:
        f.write(t+'\n')
