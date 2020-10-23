# Module imports
import requests
import json
from YelpAPI import get_api_key

# Define the API Key, Endpoint and Headers
API_KEY = get_api_key()
ENDPOINT = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization': 'bearer {}'.format(API_KEY)}


# Define the parameters
off = 0
cnt = 1

restaurants = {}

# Request to Yelp API
for i in range(20):
    PARAMETERS = {'term': 'mexican restaurants',
             'limit': 50,
             'offset': off,
             'radius': 25000,
             'location': 'Manhattan'}

    response = requests.get(url=ENDPOINT, params=PARAMETERS, headers=HEADERS)
    # Convert the json to a dictionary object
    business_data = response.json()

    for biz in business_data['businesses']:
        cuisine = []
        if biz['id'] not in restaurants:
            # restaurants[biz['id']] = biz
            if len(restaurants) == 1000:
                break
            for c in biz['categories']:
                cuisine.append(c['title'])
            restaurants[biz['id']] = [biz['id'], cuisine]
            
    print(cnt)
    off += 50
    cnt += 1

with open('mexican1.json', 'w') as outfile:
    json.dump(restaurants, outfile)

print(len(restaurants))