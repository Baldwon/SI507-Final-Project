from bs4 import BeautifulSoup
import requests
import json
import re

new_url = "https://www.airbnb.com/rooms/34071962?adults=2&check_in=2021-01-03&check_out=2021-01-05&previous_page_section_name=1000&federated_search_id=2b84e4d0-3ea6-4797-a312-96045d574112"
response = requests.get(new_url)
soup = BeautifulSoup(response.text, 'html.parser')
#print(soup) _1cnse2m

searching_div = soup.find('div',class_="_19xnuo97")
#print(len(searching_div))
# for i in searching_div:
#     print(i)
print(searching_div)