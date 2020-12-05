from bs4 import BeautifulSoup
import requests
import json
import re
import sqlite3

search_word = "new york"
checkin = "2021-01-03"
checkout = "2021-01-05" 
adult = "2"

CACHE_FILENAME = "cache.json"

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

url = "https://www.airbnb.com/s/"+search_word+"/homes?tab_id=home_tab&checkin="+checkin+"&checkout="+checkout+"&adults="+adult
print(url)

cache_dict = open_cache()
if(url in cache_dict.keys()): #cache hit

    print('Using cache')

    cache_data = cache_dict[url]

else: #cache miss

    print('Fetching')

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    info = soup.find_all(class_='_gig1e7')

    cache_data = {}

    for i in range(len(info)):
        # name
        name = info[i].find("meta",itemprop='name')
        name = str(name).split(' - null - ')[0].replace('<meta content="',"")

        # price_per_night
        price_per_night = info[i].find("span",class_='_1p7iugi')
        try:
            price_per_night = str(price_per_night).split("Price:")[1].replace('</span>','')
        except:
            price_per_night = "NULL"
        # total_price
        total_price = info[i].find(class_='_vsjqit')
        total_price = str(total_price)[str(total_price).find('$'):str(total_price).find('total<span')]

        # rating
        try:
            rating = info[i].find(class_='_18khxk1').find(class_='_krjbj')
            rating = re.findall(r'<span class="_krjbj">Rating (.+?) out of 5;</span>',str(rating))[0]
        except:
            rating = "NULL"

        # detailed_url 
        detailed_url = info[i].find("a")
        words = str(detailed_url).split()
        for word in words:
            if word.startswith('href='):
                detailed_url = word.replace('href="',"").replace('"',"")

        # location
        location = info[i].find(class_='_1tanv1h').find(class_='_167qordg')
        location = re.findall(r">(.+?)<",str(location))[0]

        # size
        size = info[i].find(class_='_kqh46o',style="margin-top:9px")
        size = re.findall(r">(.+?)<",str(size))
        size = ''.join(size).replace(' · ',',')

        # amenties
        amenities = info[i].find(class_='_kqh46o',style="margin-top:4px")
        amenities = re.findall(r">(.+?)<",str(amenities))
        amenities = ''.join(amenities).replace(' · ',',')

        conn = sqlite3.connect("hotel.sqlite")

        cur = conn.cursor()

        insert_terms = '''
                        INSERT INTO hotel_table
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''' 

        value = [name,price_per_night,total_price,rating,detailed_url,location,size,amenities]
        print(value)
        cur.execute(insert_terms, value)

        conn.commit()

        cache_data[i] = [name,price_per_night,total_price,rating,detailed_url,location,size,amenities]

    cache_dict[url] = cache_data

    save_cache(cache_dict)
    
#print(name)
#print(detailed_url)
#print(price_per_night)
#print(total_price)
#print(rating)
#print(location)
#print(size)
#print(amenities)



base_url = "https://www.airbnb.com"
#print(detailed_url)
new_url = base_url + detailed_url
print(new_url)



#ratings = searching_div.find_all(class_="_1nlbjeu")
#print(ratings)
#comments = new_soup.find_all(class_="_162hp8xh")#.find_all(class_="_1y6fhhr")
#print(comments)

