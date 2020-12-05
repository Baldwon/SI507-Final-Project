from bs4 import BeautifulSoup
import requests
import json
import re
import sqlite3

search_word = "new york"
checkin = "2020-12-05"
checkout = "2020-12-12"
url = "https://www.airbnb.com/s/" + search_word + "/experiences?&checkin=" + checkin + "&checkout=" + checkout
print(url)


CACHE_FILENAME = "ex_cache.json"

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

cache_dict = open_cache()

if(url in cache_dict.keys()): #cache hit

    print('Using cache')

    exp_dict = cache_dict[url]
    print(exp_dict.get("0"))
    for i in range(len(exp_dict)):
        title = exp_dict.get(str(i))[1]
        price = exp_dict.get(str(i))[2]
        print(title,price)

        conn = sqlite3.connect("hotel.sqlite")

        cur = conn.cursor()

        insert_terms = '''
                        INSERT INTO experience_table
                        VALUES (?, ?)
        ''' 

        value = [title,price]

        cur.execute(insert_terms, value)

        conn.commit()


else:
    print('Fetching')

    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    searching_div = soup.find(id='site-content')  

    title_raw = searching_div.find_all(class_="_1xupcs2")
    title_raw = str(title_raw).split(",")
    price_raw = searching_div.find_all("div",class_="_mi0p0f")
    print(price_raw)
    price_raw = str(price_raw).split(",")
    print(price_raw)

    print("===================")
    print(len(title_raw))
    print(len(price_raw))
    
    exp_dict = {}
    for i in range(min(len(title_raw),len(price_raw))):
        title = re.findall(r'>(.+?)</div>',str(title_raw[i]))[0]
        price = re.findall(r'From (.+?)</div>',str(price_raw[i]))[0]
        print(title)
        print(price)

        exp_dict[i] = [i,title,price]

        conn = sqlite3.connect("hotel.sqlite")

        cur = conn.cursor()

        insert_terms = '''
                        INSERT INTO experience_table
                        VALUES (?, ?)
        ''' 

        value = [title,price]

        cur.execute(insert_terms, value)

        conn.commit()
        
    if(len(title_raw)>1):
        cache_dict[url] = exp_dict
        save_cache(cache_dict)

    print(exp_dict)
        
        #what_we_will_do = searching_div.find_all("div",class_="_1db4hsw")
        


# title = searching_div.find_all(class_="_1xupcs2")
# period = searching_div.find_all(class_="_g86r3e")
# what_we_will_do = searching_div.find_all("div",class_="_1db4hsw")
# price = searching_div.find_all("div",class_="_mi0p0f")
#info = soup.find_all('a',target='_blank')



# print(title)
# print(period)
#print(what_we_will_do)
# print(price)
