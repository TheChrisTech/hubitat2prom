import json
import os
import requests
import time
import yaml
import re
import datetime

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
        for attrib  in device_details['attributes']:
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

                    # Sanitize to allow Prometheus Ingestion
                    device_name = sanitize(device_details['name'])
                    device_label = sanitize(device_details['label'])
                    device_type = sanitize(device_details['type'])
                    device_id = sanitize(device_details['id'])
                    metric_name = sanitize(attrib['name'])
                    # Create the dict that holds the data
                    device_attributes.append({
                        "device_name": f"{device_name}",
                        "device_label": f"{device_label}",
                        "device_type": f"{device_type}",
                        "device_id": f"{device_id}",
                        "metric_name": f"{prom_prefix}{metric_name}",
                        "metric_value": f"{attrib['currentValue']}",
                        "metric_timestamp": time.time()})
    # Create the response
    response = make_response(render_template('base.txt',
            device_details=device_attributes
            ))
    # Make sure we return plain text otherwise Prometheus complains
    response.mimetype = "text/plain"
    return response

def sanitize(inputValue):
    return re.sub('[^a-z0-9]+', '_', inputValue.lower())