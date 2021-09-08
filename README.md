# hubitat2prom

This application runs in a docker container, talks to the 
[Hubitat Maker API](https://docs.hubitat.com/index.php?title=Maker_API)
and returns the metrics in a format suitable for consumption by
[Prometheus](https://prometheus.io)

# Getting up and running

## Docker

Run the following command to start the container:

`docker run --name hubitat2prom -p 5000:5000 HE_URI=http://127.0.0.1/apps/api/123/devices -e HE_ACCESS_TOKEN=123456 -e HE_ATTRIBUTES=battery,humidity,illuminence,level,switch,temperature,water TheChrisTech/hubitat2prom:latest`

This will start the container listening on your local machine on port 5000, and you can visit 
[http://localhost:5000/metrics](http://localhost:5000/metrics) to confirm that the metrics are coming through.

Once you've confirmed this, you can move on to configuring Prometheus.

### ENVIRONMENT Variables:

`HE_URI` can be found on the Maker API app page, at the bottom. IP and Device ID will be different than what is shown above.

`HE_ACCESS_TOKEN` can also be found on the Maker API app page, in the example URLs at the bottom. 

`HE_ATTRIBUTES` are any attributes you wish to collect. Determine what attributes you want by visiting the Maker API app page, and clicking `Get All Devices with Full Details` link.
_default:_ battery,humidity,illuminence,level,switch,temperature

`HE_PROM_PREFIX` is the prefix for the metrics when presented to Prometheus. This helps correlate metrics together if you use Prometheus for multiple applications. 
_default:_ hubitat_

## Prometheus

Configuring Prometheus to scrape the metrics is easy.

Add the following to the bottom of your Prometheus Outputs:

```
  - job_name: 'hubitat'
    scrape_interval: 30s
    static_configs:
    - targets: ['IP-OF-Docker-Container:5000']
```

Prometheus will now scrape your web service every 30 seconds to update the metrics in the data store.

# Collected Metrics

Hubitat2Prom is capable of collecting any of the metrics that Hubitat exposes via the Maker API.

By default it will collect the list below, however adding a new metric is as simple as checking the output of the Maker API and adding the attribute name to your configuration and then restarting the service.

Some of the collections are:

```
  - battery
  - humidity
  - illuminance
  - level # This is used for both Volume AND Lighting Dimmers!
  - temperature
```
Some collections need to have their text converted to values, so they can be graphed.
```
  - switch # "on/off" is "1/0"
  - water # "wet/dry" is "1/0"
  - power # "on/off" is "1/0"
```

# Grafana

There's a sample dashboard in the [grafana/](grafana) directory that you can [import into Grafana](https://grafana.com/docs/grafana/latest/dashboards/export-import/#importing-a-dashboard) to give you an idea of what is possible!

![The sample Grafana dashboard](/screenshots/Hubitat2promOverview.png)
