import json
import boto3


def parse_lex_response(lex_resp, uid):
    timestamp = lex_resp["ResponseMetadata"]["HTTPHeaders"]["date"]
    resp_code = lex_resp["ResponseMetadata"]["HTTPStatusCode"]
    text = lex_resp["message"]
    if resp_code == 200:
        response = {
            "response_code": resp_code,
            "headers": {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "messages": [
                {
                  "type": "string",
                  "unstructured": {
                    "id": uid,
                    "text": text,
                    "timestamp": timestamp
                  }
                }
              ]
            }
    else:
        response = {
            "statusCode": resp_code,
            "headers": {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "messages": []
            }
    return response

def lambda_handler(event, context):
    # TODO implement
    client = boto3.client('lex-runtime')
    print(event)
    text = event["messages"][0]["unstructured"]["text"]
    uid = event["messages"][0]["unstructured"]["id"]
    lex_resp = client.post_text(botName='DiningSuggestions', botAlias='Prod', userId=uid, inputText=text)
    response = parse_lex_response(lex_resp, uid)
    return response
    # return {
    #     'statusCode': 200,
    #     "headers": {
    #         'Content-Type': 'application/json',
    #         'Access-Control-Allow-Origin': '*'
    #     },
    #     'body': "This is response generated from Lambda LF0"
    # }
