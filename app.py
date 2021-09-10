import json
import os
import requests
import time
import yaml
import re
from datetime import datetime

from flask import render_template, Flask, make_response

app = Flask(__name__)

base_uri = os.environ['HE_URI']
access_token = os.environ['HE_ACCESS_TOKEN']
collected_metrics = os.environ['HE_ATTRIBUTES']
prom_prefix = os.environ['HE_PROM_PREFIX']

@app.route("/metrics")

def metrics():
    devices = requests.get(f"{base_uri}?access_token={access_token}")

    device_attributes = []
    for device in devices.json():
        device_details = requests.get(f"{base_uri}/{device['id']}?access_token={access_token}").json()
        if device_details["type"] == "Google Nest Thermostat":
            nestThermostat(device_attributes, device_details)
        else:
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
    # Create the response
    response = make_response(render_template('base.txt',
            device_details_for_prom=device_attributes
            ))
    # Make sure we return plain text otherwise Prometheus complains
    response.mimetype = "text/plain"
    return response

def sanitize(inputValue):
    return re.sub('[^a-z0-9]+', '_', inputValue.lower())

def nestThermostat(device_attributes, device_details):
    for attrib in device_details['attributes']:
        # thermostatOperatingState #heating, idle, cooling  (-1, 0, 1)
        # thermostatMode # heat, off, cool, heat-cool, eco (-1, 0, 1, 2, 3)\
        if attrib["name"] == "thermostatMode":
            if attrib["currentValue"] == "heat":
                deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], -1)
                for attrib_nest in device_details['attributes']:
                    if attrib_nest["name"] == "heatingSetpoint":
                        deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib_nest['name'], attrib_nest['currentValue'])
            elif attrib["currentValue"] == "cool":
                deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], 1)
                for attrib_nest in device_details['attributes']:
                    if attrib_nest["name"] == "coolingSetpoint":
                        deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib_nest['name'], attrib_nest['currentValue'])
            elif attrib["currentValue"] == "off":
                deviceAttributes(device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], 0)
            elif attrib["currentValue"] == "eco":
                deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], 3)
                for attrib in device_details['attributes']:
                    if attrib_nest["name"] == "ecoCoolPoint":
                        deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib_nest['name'], attrib_nest['currentValue'])
                    elif attrib_nest["name"] == "ecoHeatPoint":
                        deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib_nest['name'], attrib_nest['currentValue'])
            elif attrib["currentValue"] == "heat-cool":
                deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib['name'], 2)
                for attrib in device_details['attributes']:
                    if attrib_nest["name"] == "coolingSetpoint":
                        deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib_nest['name'], attrib_nest['currentValue'])
                    elif attrib_nest["name"] == "heatingSetpoint":
                        deviceAttributes(device_attributes, device_details['name'], device_details['label'], device_details['type'], device_details['id'], attrib_nest['name'], attrib_nest['currentValue'])
        elif attrib["name"] == "thermostatOperatingState":
            if attrib["currentValue"] == "heating":
                attrib['currentValue'] = -1
            elif attrib["currentValue"] == "idle":
                attrib['currentValue'] = 0
            elif attrib["currentValue"] == "cooling":
                attrib['currentValue'] = 1
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
        "metric_timestamp": time.time()
        })