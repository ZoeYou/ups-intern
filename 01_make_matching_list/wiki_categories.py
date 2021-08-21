import requests, json, re
from IPython.display import JSON

avoid = sorted(set("""
Afghanistan African Albania Algeria Angola Arab Argentina Armenia Australia Austria Azerbaijan Bahrain Bangladesh Barbados Belgium Belize Bolivia Bosnia Botswana Brazil Brunei Bulgaria Cambodia Cameroon Canada Chad Chile China Colombia Congo Costa_Rica Croatia Cuba Cyprus Czech Denmark Djibouti Dominican Egypt Eritrea Estonia Eswatini Ethiopia Faroe_ Finland France Gabon Georgia Georgia Germany Ghana Gibraltar Greece Greenland Guyana Herzegovina Hong_Kong Hungary Iceland India Indonesia Iran Iraq Ireland Israel Italy Japan Jersey Jordan Kenya Kingdom Kosovo Kuwait Lanka Latvia Lebanon Lesotho Liberia Libya Libya Lithuania Luxembourg Madagascar Malawi Malaysia Mali Malta Marino Mauritania Mauritius Mexico Moldova Mongolia Montenegro Morocco Mozambique Myanmar Nepal Netherlands New_Zealand Nigeria Norway Oman Pakistan Palestine Panama Peru Philippines Poland Portugal Qatar Romania Russia Rwanda Saud Senegal Serbia Singapore Slovakia Slovenia Somalia Somaliland Spain Sudan Suriname Sweden Switzerland Syria Taiwan Tanzania Thailand Gambia Maldives Timor Tunisia Turkey Turkmenistan Uganda Ukraine United_States Uruguay Uzbekistan Venezuela Vietnam Yemen Zambia Zimbabwe organizations Balloon record_holders by_nationality Airships by_country by_year British Polish Mexican Belgian Canadian Austro-Hungarian Argentine Hungarian South_Africa Scottish Welsh Afghan Urdu Korean Persian Chinese Byzantine
Easter_Island Tokelau Niue Cook_Islands Tahiti Wyoming Wisconsin West_Virginia Washington,_D.C. Washington Virginia Vermont Utah Texas Tennessee Rhode_Island Pennsylvania Oregon Oklahoma Ohio New_York New_Hampshire Nevada Nebraska Montana Missouri Mississippi Minnesota Michigan Massachusetts Maryland Maine Louisiana Kentucky Kansas Iowa Illinois Idaho Hawaii Florida Delaware Connecticut Colorado California Arkansas Arizona Alaska Alabama Puerto_Rico Northern_Mariana_Islands Maya_civilization Prince_Edward_Island Nova_Scotia Newfoundland New_Brunswick Yukon Saskatchewan Ontario Nunavut Newfoundland_and_Labrador British_Columbia Alberta Mesoamerica Nicaragua Maya_civilization Honduras Guatemala El_Salvador Turks_and_Caicos_Islands Trinidad_and_Tobago Sint_Maarten Saint_Vincent_and_the_Grenadines Collectivity_of_Saint_Martin Saint_Lucia Saint_Kitts_and_Nevis Saint_Barthélemy Puerto_Rico Montserrat Martinique Jamaica Haiti Guadeloupe Grenada Dominica Cayman_Islands Curaçao British_Virgin_Islands Bonaire Bermuda Bahamas Aruba Antigua_and_Barbuda Anguilla Isle_of_Man British_Empire Wales Scotland England Spanish_East_Indies Sint_Maarten Dutch_East_Indies Bonaire Curaçao Venice Scotland England Bavaria Abkhazia Saint_Martin Saint_Barthélemy Réunion New_Caledonia Mayotte Martinique Guadeloupe French_colonial_empire Bohemia Gaza_Strip Abkhazia Sabah Dutch_East_Indies Zanzibar Kilwa_Sultanate Rivers_State Lagos_State
Danish Dutch Swedish Italian Turkish Spanish Irish Swiss Greek German French Ukrainian Slovak Krio Jewish American Argentine Belgian British Canadian Chinese English Female French German Greek Hungarian Italian Male Mexican Norwegian Polish Portuguese Puerto Rican Spanish Swedish Swiss Turkish Ukrainian    
_BC_ _beginnings _births _disestablishments _endings _war_ _wars_
accidents activists Aerospace_companies Aerospace_industry air_control air_traffic airline airport Alchemy Architect architecture Astrolog astronaut astronomer aviation award batgirl batman books business by_century by_continent Centuries_in Christmas city_hall companies_of company cosmologist cosmonaut Courthouses culture cyclone_season cyrilic dance death disaster documentary esotericism eurovision events 
faculty Fictional film Flat_Earth given_names Gotham Historic_Places History holidays in_Africa in_art in_Asia in_Europe in_fiction in_North in_South in_spaceflight internet_culture journal Kalpana killer Klingon language latin laundry layout linguistic Lists_of literature 
marriage millennium months mountains novels of_Africa of_Asia of_Europe of_North of_South participants people Phenomenology philosophy physicist Physicists police politics pop_culture post_office professorship program_of programme_of psychology radio_station religion rhythm
script Smurfs spationaut Star_Trek star_war suicide taikonaut talk_show television_series template terroris typeface typography Venezuela video_game virus Wikipedia_books years  
revolt rebellion territories Festival
Playboy Punk_ Urbanism Britpop Grunge feminism Postmodern Energy_drinks Trump_presidency Battles dynasty countries Christianity
Legion_of
tragedies comedies Dream organ_manufacturers organ_builders Watergate swimmers E_season Anime brands Celebrity dishes tennis rugby handball cricket fencing curling sports poets Hollywood Gaza designers (series) (title) (franchise) Fiction Metaphors Party Members Bodyguards fiction prisons based_on Works_by Prints_by etchers woodcarvers designers arts_of by_date by_artist by_collection draughtsmen cartoons scribes by_genre by_theme by_source by_location in_television Songs Comics lists by_period Palaces residences watches manufactured_by libraries websites chapters dishes blogs Screenshots games Military_of Dams_in Dams_on Bridges Lighthouses Proposed Subcamps prisoners Inmates Prisons residences treaties lawyers Recommendations Military_units manufacturers Ballets designers weavers vloggers libraries regions songs franchises Navy Coast_Guard Ships Steamboats submarines corvettes destroyers sloops frigates cruisers Navy vessels Shipwrecks locomotives singles players musicians songs artists albums Grand TV_series TV_series) riders 
""".lower().split()))
inre = re.compile('in \d\d+')
yearre = re.compile('^Category\:\d+s?( BC)?$|\:\d\d\d\d(s|\-related)? |in the \d\d\d\d|\d\d\d\d\-\d\d\d\d|of \d\d\d\d?|\d\d\d\d? events|\d\d\d\d? establishments|\d\d?th[- ]century|1st[- ]century|2nd[- ]century|3rd[- ]century')

def isgood(c):
    good=True
    for a in avoid:
        if a.replace('_',' ') in c.lower():
            good=False
    if inre.search(c.lower()) or yearre.search(c):
        good=False
    return good


categoriesTodo=['Category:Physics', 'Category:Technology', 'Category:Technology_by_type', 'Category:Techniques']
badcats=[]
pages={}
nbpages=0
oldnbpages=0
recentCats=[]
print('starting')

while categoriesTodo:
    category=categoriesTodo.pop(0)
    print('doing',category)
    
    cmcontinue=None
    while True: # getting all pages in the category
        payload = {'action': 'query',
               'list': 'categorymembers',
               'cmtitle': category,
               'cmdir': 'desc',
                'cmlimit': 500,
               'cmtype': 'page', # 'page'  'subcat'
               'format': 'json'
               }
        if cmcontinue:
            payload['cmcontinue']=cmcontinue
    #         print('cmcontinue',cmcontinue)
        try:
            r = requests.get('https://en.wikipedia.org/w/api.php', params=payload) # , auth=('user', 'pass')
        except:
            print("connection problem",payload)
            categoriesTodo+=[category]
            break

        cmcontinue=r.json().get('continue',{}).get('cmcontinue',None)

        for p in r.json().get('query',{}).get('categorymembers',[]):
            pages[category]=pages.get(category,[])+[p]
        if not cmcontinue:
            #print('got',len(pages.get(category,[])),'pages in',category)
            
            nbpages+=len(pages.get(category,[]))
            break
            
    while True: # getting all subcategories in the category
        payload = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': category,
                'cmdir': 'desc',
                'cmlimit': 500,
                'cmtype': 'subcat', # 'page'  'subcat'
                'format': 'json'
               }
        if cmcontinue:
            payload['cmcontinue']=cmcontinue
    #         print('cmcontinue',cmcontinue)
        try:
            r = requests.get('https://en.wikipedia.org/w/api.php', params=payload) # , auth=('user', 'pass')
        except:
            print("connection problem",payload)
            categoriesTodo+=[category]
            break
        cmcontinue=r.json().get('continue',{}).get('cmcontinue',None)

        for sc in r.json().get('query',{}).get('categorymembers',{}):
            newcat = sc['title'].replace('_',' ')
            if newcat in pages:
                continue
#             newcatunder = newcat
            if isgood(newcat):
                categoriesTodo+=[newcat]
            else:
                badcats+=[newcat]
            
        recentCats+=[category]
        if not cmcontinue:
            if nbpages-oldnbpages>10000:
#                 print('done:',' '.join(recentCats).replace('Category:',''),
                categoriesTodo=list(set(categoriesTodo))
                badcats=list(set(badcats))
                print('got',len(categoriesTodo),'categories to do.', nbpages,'pages done.')#,categoriesTodo)
                with open(str(nbpages)+'.cat.txt','w') as tempout:
                    for cc in pages:
 #                       print('cc',cc)
 #                       print(pages[cc][:33])
                        tempout.write('\t'.join([cc,'::::']+[p['title'] for p in pages[cc]])+'\n')
                with open('cat2do.txt','w') as tempout:
                    tempout.write('\n'.join(categoriesTodo)+'\n')
                with open('badcats.txt','w') as tempout:
                    tempout.write('\n'.join(sorted(badcats))+'\n')
                oldnbpages=nbpages
                recentCats=[]
            break
#     if len(pages)>5: # stop when getting enough categories
#         break
print("categoriesTodo",categoriesTodo)
print(nbpages,'pages')
print('done!')