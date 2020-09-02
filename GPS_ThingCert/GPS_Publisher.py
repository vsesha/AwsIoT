'''
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import json
import config

AllowedActions = ['both', 'publish', 'subscribe']


# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

def customSubackCallback(mid, message):
    print("Received SUBACK packet id: ")
    print(mid)
    print("Granted QoS: ")
    print(message)
    print("++++++++++++++\n\n")
    print(message.topic)


class awsClient:
    MQTTClient = None

def getCoordinateMessage():
    return "{'type': 'Polygon','Coordinates': [[[30, 10], [10, 10], [10, 0], [20, 40]]]}"

def getArgParameters():
    # Read in command-line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
    parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
    parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
    parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
    parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
    parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False, help="Use MQTT over WebSocket")
    parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub", help="Targeted client id")
    parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")
    parser.add_argument("-m", "--mode", action="store", dest="mode", default="both", help="Operation modes: %s"%str(AllowedActions))
    parser.add_argument("-M", "--message", action="store", dest="message", default="Hello World!", help="Message to publish")


def initAWS():
    # Configure logging
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    if config.useWebsocket:
        awsClient.MQTTClient = AWSIoTMQTTClient(config.clientId, useWebsocket=True)
        awsClient.MQTTClient.configureEndpoint(config.host, config.port)
        awsClient.MQTTClient.configureCredentials(config.rootCAPath)
    else:
        awsClient.MQTTClient = AWSIoTMQTTClient(config.clientId)
        awsClient.MQTTClient.configureEndpoint(config.host, config.port)
        awsClient.MQTTClient.configureCredentials(config.rootCAPath, config.privateKeyPath, config.certificatePath)



def validate():
    if config.mode not in AllowedActions:
        print("Unknown --mode option %s. Must be one of %s" % (config.mode, str(AllowedActions)))
        exit(2)

    if config.useWebsocket and config.certificatePath and config.privateKeyPath:
        print("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
        exit(2)

    if not config.useWebsocket and (not config.certificatePath or not config.privateKeyPath):
        print("Missing credentials for authentication.")
        exit(2)

    # Port defaults
    if config.useWebsocket and not config.port:  # When no port override for WebSocket, default to 443
        config.port = 443
    if not config.useWebsocket and not config.port:  # When no port override for non-WebSocket, default to 8883
        config.port = 8883



def main():
    print("Running pre-checks... ")
    validate()  

    print("Initializing AWS... ")
    initAWS()

    # AWSIoTMQTTClient connection configuration
    awsClient.MQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
    awsClient.MQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    awsClient.MQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    awsClient.MQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
    awsClient.MQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

    # Connect and subscribe to AWS IoT
    awsClient.MQTTClient.connect()


    #awsClient.MQTTClient.subscribeAsync(config.topic, 1, ackCallback=customSubackCallback)



    myMsg = getCoordinateMessage()


    # Publish to the same topic in a loop forever
    loopCount = 0
    while True:
        if config.mode == 'both':
            message = {}
            message['message'] = myMsg
            message['sequence'] = loopCount
            messageJson = json.dumps(message)
            awsClient.MQTTClient.publish(config.topic, messageJson, 1)
            if config.mode == 'both':
                print('Published topic %s: %s\n' % (config.topic, messageJson))
            loopCount += 1
            time.sleep(5)

if __name__ == "__main__":
    main()

