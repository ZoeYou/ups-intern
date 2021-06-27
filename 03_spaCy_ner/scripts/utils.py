from tqdm import tqdm
import wikipedia
import warnings
import mwparserfromhell
import wikitextparser as wtp
import requests
from collections import defaultdict   
from wasabi import msg

warnings.filterwarnings('ignore')


def find_wiki_title(term):
    """
    Using the wikipedia API to find the corresponding page title
    """
    title = wikipedia.search(term)
    if title:
        return title[0]

    
def find_wiki_summary(term):
    """
    Using the wikipedia API to find the corresponding wikipedia abstract (the first paragraph of the wikipedia page)
    """
    try:
        return wikipedia.summary(term)
    # if it is a ambiguous term, the function will return None as value of summary
    except wikipedia.exceptions.WikipediaException:
        return None


def parse(title, API_URL):
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "rvlimit": 1,
        "titles": title,
        "format": "json",
        "formatversion": "2",
        "redirects" : 1
    }
    headers = {"User-Agent": "My-Bot-Name/1.0"}
    req = requests.get(API_URL, headers=headers, params=params)
    res = req.json()
    revision = res["query"]["pages"][0]['revisions'][0]
    text = revision["slots"]["main"]["content"]
    return mwparserfromhell.parse(text)


def get_description_wiktionary(term):
    try:
        wikicode = parse(term, "https://en.wiktionary.org/w/api.php")
        parsed = wtp.parse(str(wikicode))

        for sec in parsed.sections:
            if sec.title in ['Noun', 'Proper noun'] :
                break
        description = sec.get_lists()[0].items[0]
        
        templates = wtp.parse(description).templates
        ret1 = []
        while templates:
            temp = templates.pop(0)
            if 'lb' in temp.string:
                ret1.append('('+temp.arguments[1].string[1:]+') ')
            elif 'defdate' in temp.string:
                pass
            else:
                ret1.append(temp.string.replace('|en|', ' ').strip("{").strip("}").replace('[','').replace(']',''))
        ret1 = ' '.join(ret1)   
        
        ret2 = wtp.parse(description).plain_text().strip() 
        if ret2[-1] == ':': ret2 = ret2[:-1]
        return ret1 + ret2
    
    except KeyError:
        return


def get_description_wikipedia(term):              
    try:
        wikicode = parse(term, "https://en.wikipedia.org/w/api.php")
        templates = wikicode.filter_templates()    
        flag = 0
        for temp in templates:
            if temp.name in ['short description', 'Short description']:
                flag = 1
                break
        if flag:
            return str(temp.get(1))
    except KeyError or ValueError:
        return   
     

def text_to_html(text, nlp): # gives the html under BeatifulSoup format
    doc = nlp(text)

    html = displacy.render(doc, style="ent", options={"ents": ["TERM"]}, jupyter=False, page=True)
    soup = BeautifulSoup(html)
    marks =  soup.find_all('mark')
    url = ''
    
    for mark in tqdm(marks):
        try:
            term = mark.get_text(strip=True,separator=', ').split(', ')[0] # get the term annotated
            if term in to_remove: continue
            
            wiki_info = DICT_PAGE_TITLE[term] # get wikipedia pagetitle and summary from json file
            url = f'https://en.wikipedia.org/wiki/{"_".join(wiki_info["title"].split())}' 
            summary = wiki_info['summary']
            
        except KeyError:
            wiki_title = find_wiki_title(term)  
            
            if wiki_title:
                url = f'https://en.wikipedia.org/wiki/{"_".join(wiki_title.split())}' 
                wiki_summary = find_wiki_summary(wiki_title)
                DICT_PAGE_TITLE.update({term:{'title':wiki_title, 'summary': wiki_summary}})
                    
        link = soup.new_tag('a', href=url) # create the html tag for link       
        mark.wrap(link) #add html tag <a> (the one to make links) to around our annotated word
    return soup


def text_to_json(text, nlp): # gives the ner results in json format
    to_remove = ['semiconductive material forms',
              'range',
              'more than',
              '10.',
              'successful detection',
              'smaller ratio',
              'actual payment',
              'actual price',
              'communication means',
              'independent sensors',
              'a vehicle']

    
    dict_position = defaultdict(list)
    dict_position_trigger = defaultdict(list)
    dict_res = {}
    
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == 'TERM': 
            if(ent.text in to_remove):
                continue
            elif('.\n' in ent.text): 
                term = ent.text
                end_pos = term.find('.\n')
                dict_position[term[:end_pos]].append((ent.start_char, ent.start_char+end_pos))         
            elif ('. \n' in ent.text):
                term = ent.text
                end_pos = term.find('. \n')
                dict_position[term[:end_pos]].append((ent.start_char, ent.start_char+end_pos))               
            else:
                dict_position[ent.text].append((ent.start_char, ent.end_char))
        else: # if it is a trigger word
            dict_position_trigger[ent.text].append((ent.start_char, ent.end_char))          
            
    dict_position = dict(dict_position)
    
    msg.info("Analysing errors...")
    for error, pos_l in tqdm(dict_position_trigger.items()): # only for ERROR
        dict_res.update({error: {'label': 'ERROR', 'position': pos_l}})
    msg.good("Done!")
    
    msg.info("Analysing terms...")
    cnt = 0
    for term, pos_l in tqdm(dict_position.items()): # only for TERM
        try:
            wiki_info = DICT_PAGE_TITLE[term] # get wikipedia pagetitle and summary from json file
            url = f'https://en.wikipedia.org/wiki/{"_".join(wiki_info["title"].split())}' 
            wiki_summary = wiki_info['summary'] 

        except KeyError:       
            wiki_title = find_wiki_title(term)  
            # find summary  
            try:
                ## witionary
                wiki_summary = get_description_wiktionary(term)
                if not wiki_summary:
                    ## wikipedia brief summary
                    wiki_summary = get_description_wikipedia(term)
                if (not wiki_summary) and wiki_title:
                    ## wikipedia page abstract
                    wiki_summary = find_wiki_summary(wiki_title)                  
            except KeyError:
                continue
                
            # find wiki title
            if wiki_title:
                url = f'https://en.wikipedia.org/wiki/{"_".join(wiki_title.split())}' 
                DICT_PAGE_TITLE.update({term:{'title':wiki_title, 'summary': wiki_summary}})
            else: # returns the original bad link
                url = f'https://www.wikipedia.org/{term}'
                DICT_PAGE_TITLE.update({term:{'title': '', 'summary': ''}})
                           
            cnt += 1

        dict_res.update({term:{'label': 'TERM', 'position': pos_l,'wikilink': url,'summary': wiki_summary}})
    msg.good("Done!")
    
    # update the new json of wikititle and summary 
    if cnt:
#         with open(ref_path, "w") as f: 
#             json.dump(DICT_PAGE_TITLE, f, indent = 4)
        msg.good(f"Found wikipedia information for {cnt} new terms.")
            
    return dict_res 