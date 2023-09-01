print('moo', flush=True)
import re
import requests
import google_apis
import pandas as pd
from bs4 import BeautifulSoup

def parse_address(loc_address):
    address_chunks = re.sub('<.*?>', '~', str(loc_address)).split('~')
    return {
        'address': address_chunks[1].strip(' \n'),
        'city': address_chunks[3],
        'state': address_chunks[4].strip(', ').partition(' ')[0],
        'zip': address_chunks[4].strip(', ').partition(' ')[2]
    }

def extract_location_data(location_element):
    location_data = {}
    
    try:
        loc_name = location_element.find('u').text
    except:
        # print('loc_name error')
        # print(location_element)
        loc_name = 'ERROR'
    location_data['name'] = loc_name

    try:
        loc_address_html = location_element.find_all('font')[1]
        address_data = parse_address(loc_address_html)
    except:
        # print('loc_address error')
        # print(location_element)
        address_data = {
            'address': 'ERROR',
            'city': 'ERROR',
            'state': 'ERROR',
            'zip': 'ERROR'
        }
    location_data.update(address_data)

    try:
        loc_url = 'https://www.dinersdriveinsdiveslocations.com/' + location_element.find('a')['href']
    except:
        # print('loc_url error')
        # print(location_element)
        loc_url = 'ERROR'
    location_data['url'] = loc_url

    return location_data



def get_location_elements(soup):
    centers = [
        center
        for center
        in soup.find_all('center')
        if center.find('table')
    ]
    assert len(centers)==1
    raw_location_elements = centers[0].find_all('td')
    location_elements = [
        location_element
        for location_element
        in raw_location_elements
        if not location_element.find('div')
    ]
    return location_elements


with open('ddd_urls.txt') as uf:
    lines = uf.readlines()
    state_urls = [line.strip('\n') for line in lines]

locations = []

for url in state_urls:
    print(f"Scraping {url}... ", end='', flush=True)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    location_elements = get_location_elements(soup)
    
    new_locations = [
        extract_location_data(location_element)
        for location_element
        in location_elements
    ]
    
    locations.extend(new_locations)
    print("Success!")

ddd_locs = pd.DataFrame(locations)

print('making full_addresses')
ddd_locs['full_address'] = ddd_locs['address'] + ', ' + ddd_locs['city'] + ', ' + ddd_locs['state'] + ' ' + ddd_locs['zip']

def resolve_addresses(row):
    address = row['full_address']
    print(address, flush=True)
    lat, lon = google_apis.get_lat_lon(address)
    return lat, lon

ddd_locs[['latitude', 'longitude']] = ddd_locs[['full_address']].apply(resolve_addresses, axis=1, result_type='expand')
ddd_locs.to_csv('ddd_locations.csv', index=False)


