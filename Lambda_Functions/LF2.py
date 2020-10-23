import json
import boto3
import random
# import requests
from botocore.vendored import requests
from requests_aws4auth import AWS4Auth
import os

def get_sqs_message_attributes(msg):
    # return msg['MessageAttributes'][attr]['StringValue']
    message_attributes = {}
    message_attributes['cuisine'] = msg['MessageAttributes']['cuisine']['StringValue']
    message_attributes['date'] = msg['MessageAttributes']['date']['StringValue']
    message_attributes['location'] = msg['MessageAttributes']['location']['StringValue']
    message_attributes['numPeople'] = msg['MessageAttributes']['numPeople']['StringValue']
    message_attributes['phone'] = msg['MessageAttributes']['phone']['StringValue']
    message_attributes['time'] = msg['MessageAttributes']['time']['StringValue']
    return message_attributes

def get_sqs_queue_messages():
    # Create SQS client
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/673982206489/suggestionsQueue'
    
    # Receive message from SQS queue
    response = sqs.receive_message(
                QueueUrl=queue_url,
                AttributeNames=[
                    'SentTimestamp'
                ],
                MaxNumberOfMessages=2,
                MessageAttributeNames=[
                    'All'
                ],
                VisibilityTimeout=10,
                WaitTimeSeconds=0
                )
    print("Debug: SQS response is:", response)
    if "Messages" in response.keys():
        message_list = response['Messages']
    else:
        message_list = []
    return message_list

def delete_sqs_messages(receipt_handle):
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/673982206489/suggestionsQueue'
    sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

def get_restaurant_ids_elasticsearch(cuisine):
    print("Elastic Search")
    region = 'us-east-1' 
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    endpoint = 'https://search-yelp-restaurants-o4d7ack43ubxvnsu3h2y4od4ym.us-east-1.es.amazonaws.com/'
    index = 'restaurants'
    url = endpoint + index + '/_search'
    query = {
        "size": 10,
        "query": {
            "query_string": {
              "default_field": "cuisine",
              "query": cuisine
            }
        }
    }

    headers = { "Content-Type": "application/json" }

    response = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    recommendations =  json.loads(response.text)
    print("Debug: Elasticsearch response is",recommendations)
    restaurant_id_list = [res["_source"]['restaurant_id'] for res in recommendations["hits"]["hits"]]
    return restaurant_id_list

def get_restaurant_details(restaurants):
    print("Debug: Fetching from Dynamo DB")
    restaurant_list = []
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp_restaurants')
    for restaurant in restaurants:
        response = table.get_item(Key={'restaurant_id' : restaurant})
        restaurant_list.append(response)
    print("Debug: List of restaurants fetched from DynamoDB: ",restaurant_list)
    return restaurant_list

def parsed_restaurant_details(restaurant_details):
    restaurant_text = ''
    count = 3 if len(restaurant_details) >= 3 else len(restaurant_details)
    restaurants = random.sample(restaurant_details, count)
    print("Debug: Restuarants from DynamoDB:", restaurants)
    for i, restaurant in enumerate(restaurants):
        restaurant_name = restaurant['Item']['restaurantName']
        restaurant_address = restaurant['Item']['address']
        restaurant_text +=  '{0}. {1} located at {2}.'.format((i+1), restaurant_name, restaurant_address)
    return restaurant_text
    
def send_text_message(phone_num, text):
    client = boto3.client('sns')
    response = client.publish(PhoneNumber=phone_num, Message=text)

def lambda_handler(event, context):
    sqs_messages = get_sqs_queue_messages()
    for msg in sqs_messages:
        receipt_handle = msg['ReceiptHandle']
        message_attributes = get_sqs_message_attributes(msg)
        print("Debug: Message attributes from SQS are: ",message_attributes)
        restaurant_id_list = get_restaurant_ids_elasticsearch(message_attributes['cuisine'])
        if restaurant_id_list:
            restaurant_details = get_restaurant_details(restaurant_id_list)
            restaurant_recommendations = parsed_restaurant_details(restaurant_details)
            print("Debug: Restaurant suggestions are:",restaurant_recommendations)
            text_message = "Hello! Here are your {0} restaurant suggestions for {1} people, for {2} {3} : {4}".format(message_attributes['cuisine'], message_attributes['numPeople'], message_attributes['date'], message_attributes['time'], restaurant_recommendations) 
        else:
            text_message = "Sorry, we were unable to find any restaurants for {0} cuisine in {1} for {2} at the requested time. We regret for the inconvenience".format(message_attributes['cuisine'], message_attributes['location'], message_attributes['numPeople'])
        print("Debug: The text message is: ",text_message)
        phone_num = message_attributes['phone']
        if "+1" not in phone_num:
            phone_num  = '+1'+phone_num
        print('Debug: Phone number is ',phone_num)
        send_text_message(phone_num, text_message)
        delete_sqs_messages(receipt_handle)
