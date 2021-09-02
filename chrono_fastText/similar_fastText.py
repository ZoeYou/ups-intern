import fasttext
import io
import operator
import numpy as np
from tqdm import tqdm


def make_fastText(list_terms, tgt_file, model):
    #with open(list_file, 'r') as in_f:
    #    terms = in_f.readlines()
    #    terms = [term.strip() for term in terms]
    terms = list_terms
   
    print('making fastText...')
    with open(tgt_file, 'w') as out_f:
        for term in tqdm(terms):
            vec = model.get_word_vector(term)
            out_f.write(term.replace(' ','_') + ' ')
            out_f.write(' '.join(np.array(vec).astype('str')) + '\n')
    

def save_vectors(fname):
    fin = io.open(fname, 'r', encoding='utf-8', newline='\n', errors='ignore')
    #n, d = map(int, fin.readline().split())
    terms = []
    vecs = []

    print('Saving vectors...')
    for line in tqdm(fin):
        tokens = line.rstrip().split(' ')
        terms.append(tokens[0])
        vecs.append(tokens[1:])
    
    #save embedding table
    np.save('tgt_terms_vec.npy', np.array(vecs).astype('float16'))

    #save list of terms
    with open('tgt_terms.txt', 'w') as f:
        for t in terms:
            f.write("%s\n" % t.replace('_',' '))
  

def load_vectors(term_file, vec_file):
    with open(term_file) as f:
        terms = f.read().splitlines()
    vecs = np.load(vec_file)
    return terms, vecs
    

def most_similar(term, tgt_terms, emb_mat, ft_model, n=10):
    term_vec = np.array(ft_model.get_word_vector(term))
    similarity_scores = emb_mat.dot(term_vec)/ (np.linalg.norm(emb_mat, axis=1) * np.linalg.norm(term_vec))

    term_score = list(zip(tgt_terms, similarity_scores))
    term_score.sort(key=operator.itemgetter(1), reverse=True)

    res = [tgt[0] for tgt in term_score[:10] if tgt[0] != term]
    return res

    
ft_model = fasttext.load_model('wiki.en.bin')

with open('wiki_terms.txt', 'r') as f:
    list_wiki = f.read().splitlines()

with open('all_terms_unique.txt', 'r') as f:
    list_cpc = f.read().splitlines()


#make_fastText(list_terms = list(set(list_cpc + list_wiki)), tgt_file = 'tgt.en.vec', model = ft_model)
#save_vectors('tgt.en.vec')
terms, vecs = load_vectors(term_file='tgt_terms.txt', vec_file='tgt_terms_vec.npy')


src_terms = ['machine learning', 'support vector machine', 'artificial intelligence', 'data science', 'computer science', 'scrollable refresh trigger', 'method of claim', 'scroll command']

import time
time_start = time.time()
for t in src_terms: 
    res = most_similar(t, terms, vecs, ft_model, n=10)

    print(t)
    print(res)
time_end=time.time()
print('time cost',(time_end-time_start)/len(src_terms), 's')
