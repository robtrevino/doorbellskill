# -*- coding: utf-8 -*-

# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Alexa Smart Home Lambda Function Sample Code.

This file demonstrates some key concepts when migrating an existing Smart Home skill Lambda to
v3, including recommendations on how to transfer endpoint/appliance objects, how v2 and vNext
handlers can be used together, and how to validate your v3 responses using the new Validation
Schema.

Note that this example does not deal with user authentication, only uses virtual devices, omits
a lot of implementation and error handling to keep the code simple and focused.
"""

import logging
import time
import json
import uuid
import boto3
import requests
import decimal

# Imports for v3 validation
from validation import validate_message

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_uuid():
    return str(uuid.uuid4())

def lambda_handler(event, context):
    print(str(event))
    #print(str(context))
    #access_token = event['directive']['payload']['scope']['token']

    if event['directive']['header']['namespace'] == 'Alexa.Discovery':
        return handleDiscovery(context, event)
    elif event['directive']['header']['namespace'] == 'Alexa.Authorization':
        return handleAuthorization(context, event)


##### The Handlers #########
def handleDiscovery(context, event):
    payload = ''
    header = {
        "namespace": "Alexa.Discovery",
        "name": "Discover.Response",
        "payloadVersion": "3",
        "messageId" : get_uuid()
        }

    if event['directive']['header']['name'] == 'Discover':
        payload = {
            'endpoints':
            [
                {
                    "endpointId": "dashbuttondoorbell",
                    "manufacturerName": "Amazon",
                    "friendlyName": "front door",
                    "description": "Hacked dash button to work as doorbell",
                    "displayCategories": ["DOORBELL"],
                    "cookie": {},
                    "capabilities": [
                        {
                            "type": "AlexaInterface",
                            "interface": "Alexa.DoorbellEventSource",
                            "version": "3",
                            "proactivelyReported": True
                        }
                    ]
                }
            ]
        }
        return { 'event': {'header': header, 'payload': payload }}


def handleAuthorization(context,event):
        if event['directive']['header']['name'] == "AcceptGrant":
            ### get first token from oauth
            url = 'https://api.amazon.com/auth/o2/token'
            headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
            params = {
                'grant_type': 'authorization_code',
                'code' : event['directive']['payload']['grant']['code'],
                'client_id' : 'PUT CLIENT ID HERE',
                'client_secret': 'PUT CLIENT SECRET HERE'
            }
            r = requests.post(url=url, headers=headers, data=params)

            access_token = r.json()
            access_token['received'] = decimal.Decimal(time.time())

            ### need to store the token ###
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('doorbelltokens')
            table.put_item(
                Item={
                    'user': 'roberto',
                    'grant': event['directive']['payload']['grant'],
                    'grantee': event['directive']['payload']['grantee'],
                    'access_token' : access_token
                }
            )
            response = {
                "event": {
                    "header": {
                        "namespace": "Alexa.Authorization",
                        "name": "AcceptGrant.Response",
                        "payloadVersion": "3",
                        "messageId": get_uuid()
                    },
                    "payload": {}
                }
            }
            print(str(response))
            return response
