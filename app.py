import json
import os
import requests
import time
import yaml
import re
from datetime import datetime
import sys

from flask import render_template, Flask, make_response

app = Flask(__name__)

base_uri = os.environ['HE_URI']
access_token = os.environ['HE_ACCESS_TOKEN']
collected_metrics = os.environ['HE_ATTRIBUTES']
prom_prefix = os.environ['HE_PROM_PREFIX']

device_attributes = []
timestamp_to_use = time.time()

@app.route("/metrics")

def metrics():
    devices = requests.get(f"{base_uri}?access_token={access_token}")
    for device in devices.json():
        device_details = requests.get(f"{base_uri}/{device['id']}?access_token={access_token}").json()
        if device_details["type"] == "Google Nest Thermostat":
            nestThermostat(device_attributes, device_details)
        for attrib in device_details['attributes']:
            # Is this a metric we should be collecting?
            if attrib["name"] in collected_metrics:
                # Does it have a "proper" value?
                if attrib["currentValue"] is not None:
                    # If it's a switch, then change from text to binary values
                    if attrib["name"] in ["switch", "power", "water"] :
                        if attrib["currentValue"] in ["on", "wet"]:
                            attrib["currentValue"] = 1
                        elif attrib["currentValue"] in ["off", "dry"]:
                            attrib["currentValue"] = 0
                        else:
                            attrib["currentValue"] = attrib["currentValue"]
                    deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], attrib['currentValue'])
    
    # This code removes duplicates - No idea why some things are entered twice.
    output_list = []
    for i in range(len(device_attributes)):
        if device_attributes[i] not in device_attributes[i + 1:]:
            output_list.append(device_attributes[i])

    # Create the response
    response = make_response(render_template('base.txt',
            device_details_for_prom=output_list
            ))
    # Make sure we return plain text otherwise Prometheus complains
    response.mimetype = "text/plain"
    return response

def sanitize(inputValue):
    return re.sub('[^a-z0-9]+', '_', inputValue.lower())

def nestThermostat(device_attributes, device_details):
    mode = 0
    for attrib in device_details['attributes']:
        # thermostatOperatingState #cooling, idle, heating  (-1, 0, 1)
        # thermostatMode # cool, off, heat, heat-cool, eco (-1, 0, 1, 2, 3)
        if attrib["name"] == "thermostatMode":
            if attrib["currentValue"] == "cool":
                mode = -1
            elif attrib["currentValue"] == "off":
                mode = 0
            elif attrib["currentValue"] == "heat":
                mode = 1
            elif attrib["currentValue"] == "heat-cool":
                mode = 2
            elif attrib["currentValue"] == "eco":
                mode = 3
            deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], mode)
        elif attrib["name"] == "thermostatOperatingState":
            if attrib["currentValue"] == "cooling":
                attrib['currentValue'] = -1
            elif attrib["currentValue"] == "heating":
                attrib['currentValue'] = 1
            else:
                attrib['currentValue'] = 0
            deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], attrib['currentValue'])
    
    for attrib in device_details['attributes']:
        if mode == -1 or mode == 2:
            if attrib["name"] == "coolingSetpoint":
                deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], attrib['currentValue'])
        if mode == 1 or mode == 2:
            if attrib["name"] == "heatingSetpoint":
                deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], attrib['currentValue'])
        if mode == 3:
            if attrib["name"] == "ecoCoolPoint":
                deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], attrib['currentValue'])
            elif attrib["name"] == "ecoHeatPoint":
                deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], attrib['currentValue'])

def deviceAttributes(device_attributes, device_name, device_label, device_type, device_id, metric_name, metric_value):
    # Sanitize to allow Prometheus Ingestion
    device_name_clean = sanitize(device_name)
    device_label_clean = sanitize(device_label)
    device_type_clean = sanitize(device_type)
    device_id_clean = sanitize(device_id)
    metric_name_clean = sanitize(metric_name)
    # Append to the dict that holds the data
    device_attributes.append({
        "device_name": f"{device_name_clean}",
        "device_label": f"{device_label_clean}",
        "device_type": f"{device_type_clean}",
        "device_id": f"{device_id_clean}",
        "metric_name": f"{prom_prefix}{metric_name_clean}",
        "metric_value": f"{metric_value}",
        "metric_timestamp": timestamp_to_use
        })