"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages reservations for hotel rooms and car rentals.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'BookTrip' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""

import json
import datetime
from datetime import date
from datetime import datetime
import time
import os
import dateutil.parser
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    print("Debug: Session attr: ",session_attributes)
    if not message['content']:
        return {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'intentName': intent_name,
                'slots': slots,
                'slotToElicit': slot_to_elicit
            }
        }
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---

def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


# --------------------- Validation driver function ---------------------

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

# --------------------- Validation functions for each slot ---------------------

def isvalid_location(location):
    locations = ['new york', 'manhattan']
    if not location:
        return build_validation_result(False,
                               'Location',
                               '')
    if location.lower() not in locations:
        return build_validation_result(False,
                                       'Location',
                                       'Please enter a location in Manhattan')
    return build_validation_result(True,'','')

def isvalid_cuisine(cuisine):
    if not cuisine :
        return build_validation_result(False,
                                       'Cuisine',
                                       '')
    cuisines = ['indian','thai','american','chinese','italian','mexican']
    if cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'Cuisine',
                                       'This cuisine is not available')
    print("Debug: cuisine is: ",cuisine)
    return build_validation_result(True,'','')
    
    
def isvalid_date(date1):
    if not date1:
        return build_validation_result(False,'DiningDate','')
    curr_date = str(date.today())
    curr_date1 = time.strptime(curr_date, "%Y-%m-%d")
    newdate1 = time.strptime(date1, "%Y-%m-%d")
    print('Debug old date:', date1)
    print('Debug new date:', newdate1)
    print('Current date:', curr_date1)
    print(newdate1 < curr_date1)
    
    # end_date = curr_date + datetime.timedelta(days=30)
    try:
        if newdate1 < curr_date1:
            print('validation failed in this block')
            return build_validation_result(False,'DiningDate','Please enter a valid Dining Date')
        print('Date is:', dateutil.parser.parse(date1))
        dateutil.parser.parse(date1)
        
        return build_validation_result(True,'','')
        # return True
    except ValueError:
        return build_validation_result(False,'DiningDate','Please enter a valid Dining Date')
        # return False

    
def isvalid_time(time, date1):
    print("Debug: time is:",time)
    date2 = date1[:10]
    if not time:
        return build_validation_result(False,'DiningTime','')
    
    if time:
        if date2 == str(date.today()):
            print("Debug: date entered is same as current day")
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            if time <= current_time:
                print("It's reaching here!")
                return build_validation_result(False,'DiningTime','Please enter a valid Dining Time')
            else:
                return build_validation_result(True,'','')
        else:
            return build_validation_result(True,'','')
    return build_validation_result(False,'DiningTime','Please enter a valid Dining Time')

def isvalid_people(num_people):
    if not num_people:
         return build_validation_result(False,'NumberPeople','')
    num_people = int(num_people)
    if num_people > 50 or num_people < 1:
        return build_validation_result(False,
                                  'NumberPeople',
                                  'Range of 1 to 50 people allowed')
    return build_validation_result(True,'','')

def isvalid_phonenum(phone_num):
    if not phone_num:
        return build_validation_result(False, 'PhoneNumber', '')
    if len(phone_num)!= 10 and (phone_num.startswith('+1') is False and len(phone_num) != 12):
        return build_validation_result(False, 'PhoneNumber', 'Phone Number must be in form +1xxxxxxxxxx or a 10 digit number')
    elif len(phone_num) == 10 and (phone_num.startswith('+1') is True):
        return build_validation_result(False, 'PhoneNumber', 'Phone Number must be in form +1xxxxxxxxxx or a 10 digit number')
    return build_validation_result(True,'','')


def validate_reservation(restaurant):
    
    location = restaurant['Location']
    cuisine = restaurant['Cuisine']
    diningdate = restaurant['DiningDate']
    diningtime = restaurant['DiningTime']
    numberpeople = restaurant['NumberPeople']
    phonenumber = restaurant['PhoneNumber']

    if not location or not isvalid_location(location)['isValid']:
        return isvalid_location(location)
    
    if not cuisine or not isvalid_cuisine(cuisine)['isValid']:
        return isvalid_cuisine(cuisine)
        
    if not diningdate or not isvalid_date(diningdate)['isValid']:
        return isvalid_date(diningdate)
        
    if not diningtime or not isvalid_time(diningtime, diningdate)['isValid']:
        return isvalid_time(diningtime, diningdate)
        
    if not numberpeople or not isvalid_people(numberpeople)['isValid']:
        return isvalid_people(numberpeople)
        
    if not phonenumber or not isvalid_phonenum(phonenumber)['isValid']:
        return isvalid_phonenum(phonenumber)
        
    # return True json if nothing is wrong
    return build_validation_result(True,'','')


def restaurantSQSRequest(requestData):
    
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/673982206489/suggestionsQueue'
    delaySeconds = 5
    messageAttributes = {
        'cuisine': {
            'DataType': 'String',
            'StringValue': requestData['Cuisine']
        },
        'location': {
            'DataType': 'String',
            'StringValue': requestData['Location']
        },
        'date': {
            'DataType': 'String',
            'StringValue': requestData['DiningDate']
        },
        "time": {
            'DataType': "String",
            'StringValue': requestData['DiningTime']
        },
        'numPeople': {
            'DataType': 'Number',
            'StringValue': requestData['NumberPeople']
        },
        'phone': {
            'DataType' : 'String',
            'StringValue' : requestData['PhoneNumber']
        }
    }
    messageBody=('Recommendation for the food')
    
    response = sqs.send_message(
        QueueUrl = queue_url,
        DelaySeconds = delaySeconds,
        MessageAttributes = messageAttributes,
        MessageBody = messageBody
        )

    print("response", response)
    
    print ('send data to queue')
    print(response['MessageId'])
    
    return response['MessageId']

def make_restaurant_reservation(intent_request):
    """
    Performs dialog management and fulfillment for booking a hotel.

    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """
    print("Debug: Entered make_restaurant_reservation" )
    location = try_ex(lambda: intent_request['currentIntent']['slots']['Location'])
    print("Debug: Location is  ",location)
    cuisine = try_ex(lambda: intent_request['currentIntent']['slots']['Cuisine'])
    diningdate = try_ex(lambda: intent_request['currentIntent']['slots']['DiningDate'])
    diningtime = try_ex(lambda: intent_request['currentIntent']['slots']['DiningTime'])
    numberpeople = try_ex(lambda: intent_request['currentIntent']['slots']['NumberPeople'])
    phonenumber = try_ex(lambda: intent_request['currentIntent']['slots']['PhoneNumber'])

    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    # Load confirmation history and track the current reservation.
    reservationJson = json.dumps({
        'Location': location,
        'Cuisine': cuisine,
        'DiningDate': diningdate,
        'DiningTime': diningtime,
        'NumberPeople': numberpeople,
        'PhoneNumber':phonenumber
    })
    reservation = json.loads(reservationJson)
    # session_attributes['currentReservation'] = reservation

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_reservation(reservation)
        print("Debug: Validation result is: ", validation_result)
        if not validation_result['isValid']:
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None
            print(elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            ))
            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Otherwise, let native DM rules determine how to elicit for slots and prompt for confirmation.  Pass price
        # back in sessionAttributes once it can be calculated; otherwise clear any setting from sessionAttributes.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

        print("output_session_attributes", output_session_attributes)
        
        # return delegate(output_session_attributes, intent_request['currentIntent']['slots'])
      
    requestData = {
                    'Location': location,
                    'Cuisine': cuisine,
                    'DiningDate': diningdate,
                    'DiningTime': diningtime,
                    'NumberPeople': numberpeople,
                    'PhoneNumber':phonenumber
                }
                
    # print (requestData)
    
    
    messageId = restaurantSQSRequest(requestData)
    print ("Debug: messageId:",messageId)

    return close(intent_request['sessionAttributes'],
             'Fulfilled',
             {'contentType': 'PlainText',
              'content': 'I have received your request and will be sending the suggestions shortly. Have a Great Day !!'})

# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return make_restaurant_reservation(intent_request)
    
    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
