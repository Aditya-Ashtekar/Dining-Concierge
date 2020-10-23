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
        if biz['id'] not in restaurants:
            # restaurants[biz['id']] = biz
            if len(restaurants) == 1000:
                break
            restaurants[biz['id']] = [biz['id'], biz['name'], biz['location']['address1'],
                                      biz['coordinates'], biz['review_count'],
                                      biz['rating'], biz['location']['zip_code']]
            
    print(cnt)
    off += 50
    cnt += 1

with open('mexican.json', 'w') as outfile:
    json.dump(restaurants, outfile)

print(len(restaurants))