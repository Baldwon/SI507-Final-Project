from bs4 import BeautifulSoup
import requests
import json
import re
import sqlite3
import plotly.graph_objs as go 
from plotly import subplots

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

def search_hotel_item(search_word,checkin,checkout,adult):
    ''' search hotel item (fetch or cache) and return essential information, based on search_word, checkin, checkout, and adult

    Parameters
    ----------
    search_word: string
        The word to search

    checkin: string
        The check-in date

    checkout: string
        The check-out date

    adult: string
        The number of adults
    
    Returns
    -------
    cache_data: dict
        It includes different hotel's list of name,price_per_night,total_price,rating,detailed_url,location,size,amenities

    '''
    url = "https://www.airbnb.com/s/"+search_word+"/homes?tab_id=home_tab&checkin="+checkin+"&checkout="+checkout+"&adults="+adult
    

    cache_dict = open_cache()
    if(url in cache_dict.keys()): #cache hit

        print('Using cache')

        cache_data = cache_dict[url]

        return cache_data

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
            try:
                total_price = info[i].find(class_='_vsjqit')
                total_price = str(total_price)[str(total_price).find('$'):str(total_price).find('total<span')]
            except:
                total_price = "NULL"

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

            # save the info to sql

            conn = sqlite3.connect("airbnb.sqlite")

            cur = conn.cursor()

            create_terms = '''
                CREATE TABLE IF NOT EXISTS "hotel_table"(
	                "name"	TEXT,
	                "price_per_night"	TEXT,
	                "total_price"	TEXT,
	                "rating"	TEXT,
	                "detailed_url"	TEXT,
	                "location"	TEXT,
	                "size"	TEXT,
	                "amenties"	TEXT
                );
            '''

            insert_terms = '''
                            INSERT INTO hotel_table
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''' 

            value = [name,price_per_night,total_price,rating,detailed_url,location,size,amenities]

            cur.execute(create_terms)

            cur.execute(insert_terms, value)

            conn.commit()

            cache_data[str(i)] = [name,price_per_night,total_price,rating,detailed_url,location,size,amenities]

        cache_dict[url] = cache_data

        save_cache(cache_dict)

        return cache_data
    
def search_experience_item(search_word, checkin, checkout):
    ''' search experience item (fetch or cache) and return essential information, based on search_word, checkin, checkout
    
    Parameters
    ----------
    search_word: string
        The word to search

    checkin: string
        The check-in date

    checkout: string
        The check-out date
    
    Returns
    -------
    exp_dict: dict
        It includes different experience's list of title and detailed URL

    '''
    cache_dict = open_cache()
    url = "https://www.airbnb.com/s/" + search_word + "/experiences?&checkin=" + checkin + "&checkout=" + checkout


    if(url in cache_dict.keys()): #cache hit
        print('Using cache')

        exp_dict = cache_dict[url]
        return exp_dict

    else: # cache miss
        print('Fetching')
    
        response = requests.get(url)

        # scrape html, and we need to clean and parse data
        soup = BeautifulSoup(response.text, 'html.parser')
        searching_div = soup.find(id='site-content')  
        raw_data = str(searching_div.find_all(class_="_sqvp1j")).split('</a>')
        del raw_data[-1]
        title_list = []
        detailed_url_list = []
        for i in range(len(raw_data)):
            title = re.findall(r'aria-label="(.+?)" class="_sqvp1j"',raw_data[i])
            detailed_url = re.findall(r'href="(.+?)" rel="',raw_data[i])

            if(title != [] and detailed_url!= []):
                if(len(title[0])>1 and len(detailed_url[0])>1):
                    title_list.append(title[0])
                    detailed_url_list.append(detailed_url[0])
        
        exp_dict = {}

        for i in range(len(title_list)):
            # assign title and detailed url to dictionary
            exp_dict[str(i)] = [title_list[i],detailed_url_list[i]]

            conn = sqlite3.connect("airbnb.sqlite")

            cur = conn.cursor()

            create_terms = '''
                CREATE TABLE IF NOT EXISTS "experience_table"(
	                "title"	TEXT,
	                "detailed_url"	TEXT
                );
            '''

            insert_terms = '''
                            INSERT INTO experience_table
                            VALUES (?, ?)
            ''' 

            value = [title_list[i],detailed_url_list[i]]

            cur.execute(create_terms)

            cur.execute(insert_terms, value)

            conn.commit()
    
        if(len(title_list)>1):
            cache_dict[url] = exp_dict
            save_cache(cache_dict)

        return exp_dict



if __name__ == "__main__":
    while True:
        service_type = input("What type service do you want to find? <Hint: hotel or experience>\n")
        if(service_type == 'hotel' or service_type == 'experience'):
            if(service_type == 'hotel'):
                search_word = input("What is your search word? <Hint: new york>\n")
                checkin = input("What is your check in date? <Hint: 2021-01-03>\n")
                checkout = input("What is your check out date? <Hint: 2021-01-05>\n")
                adult = input("What is the number of adult? <Hint: 2>\n")

                cache_data = search_hotel_item(search_word,checkin,checkout,adult)
                name_rating_vals = []
                rating_vals = []
                name_price_vals = []
                price_per_night_vals = []

                for i in range(len(cache_data)):
                    [name,price_per_night,total_price,rating,detailed_url,location,size,amenities] = cache_data.get(str(i))
                    print("--------------------------------------------------------------")
                    print("[%d]\n|name:%s\n|price/night:%s\n|rating:%s\n|location:%s\n|size:%s\n|amentities:%s\n|hotel_url:%s" %(i+1,name,price_per_night,rating,location,size,amenities,"https://www.airbnb.com"+str(detailed_url)))
                    print("--------------------------------------------------------------")
                    if(name != "NULL" and rating != "NULL"): 
                        name_rating_vals.append(name)
                        rating_vals.append(float(rating))
                        
                    if(name != "NULL" and price_per_night != "NULL"):
                        name_price_vals.append(name)
                        price_per_night_vals.append(float(price_per_night[1:].replace(',','')))

                trace_0 = go.Bar(x=name_rating_vals, y=rating_vals)
                trace_1 = go.Bar(x=name_price_vals, y=price_per_night_vals)
                fig = subplots.make_subplots(rows=1,cols=2,subplot_titles=["rating","price/night"])
                fig.append_trace(trace_0,1,1)
                fig.append_trace(trace_1,1,2)
                fig.show()
                exit()

            elif(service_type == 'experience'):
                search_word = input("What is your search word? <Hint: new york>\n")
                checkin = input("What is your check in date? <Hint: 2021-01-03>\n")
                checkout = input("What is your check out date? <Hint: 2021-01-05>\n")

                exp_dict = search_experience_item(search_word,checkin,checkout)

                for i in range(len(exp_dict)):

                    [title,detailed_url] = exp_dict.get(str(i))
                    print("--------------------------------------------------------------")
                    print("[%d]\n|title:%s\n|experience_url:%s" %(i+1,title,"https://www.airbnb.com"+str(detailed_url)))
                    print("--------------------------------------------------------------")
                exit()
        else:
            print("the service type is wrong, please select again.\n")
