#!/usr/bin/env python

"""upa.py: microplane alert. Checks sdr ultrafeeder output
for interesting planes and issues notifications."""

import datetime

# import json
import os
import time

import apprise
import orjson
import requests


def build_database():
    import io

    print("Downloading alert csv")
    # The csv format only requires a list of ICAO/Hex in the first column
    # everything else isn't retained or used

    database_url = os.environ.get(
        "UPA_PADATABASE_URL",
        "https://github.com/sdr-enthusiasts/plane-alert-db/raw/main/plane-alert-db.csv",
    )
    r = requests.get(
        database_url,
        timeout=5,
    )
    csvfile = io.StringIO(r.text)
    global padb
    padb = {line.split(",")[0]: 0 for line in csvfile}


def poll_planes(json_url):
    print("Starting a polling loop")
    response = requests.get(json_url, timeout=5)
    adsbdata = orjson.loads(response.text)
    global jsontimestamp  # Needs to be global as it's not in the plane object
    jsontimestamp = int(adsbdata["now"])
    # The json file format is a nest of all of the planes under 'aircraft'
    # So we need to loop through each entity in aircraft
    for plane in adsbdata["aircraft"]:
        # If we don't have a position, skip this plane.
        if planealert(plane):
            notify(plane)


def planealert(plane):
    icao = plane.get("hex", "").upper()
    twohoursago = jsontimestamp - 7200
    if padb.get(icao, jsontimestamp) >= twohoursago:
        return False
    padb[icao] = jsontimestamp
    return True


def planespotter(icao):
    planespotter_url = f"https://api.planespotters.net/pub/photos/hex/{icao}"
    planeresponse = requests.get(planespotter_url, timeout=5)
    planespotterdb = orjson.loads(planeresponse.text)
    if planespotterdb["photos"]:
        return planespotterdb["photos"][0]["link"]
    return False


def notify(plane):
    # Build variables first
    icao = plane.get("hex", "").upper()
    registration = (plane["r"].upper().strip()) if "r" in plane.keys() else False
    operator = (
        (plane["ownOp"].upper().strip().replace(" ", "_"))
        if "ownOp" in plane.keys()
        else ""
    )
    if "desc" in plane.keys():
        planetype = plane["desc"].strip()
    elif "t" in plane.keys():
        planetype = plane["t"].upper().strip()
    else:
        planetype = False
    flight = (plane["flight"].upper().strip()) if "flight" in plane.keys() else False
    jsontoday = datetime.datetime.fromtimestamp(jsontimestamp, datetime.UTC).strftime(
        "%Y-%m-%d"
    )

    photourl = planespotter(icao)

    # And now check if they have a value and if so add to notification
    nplanetype = f"A {planetype} " if planetype else "A plane "
    noperator = f"operated by #{operator} " if operator else ""
    nicao = f"has been detected with ICAO #{icao}, " if icao else ""
    nregistration = f"Registration #{registration} " if registration else ""
    nflight = f"operating Flight Number #{flight}. " if flight else ""
    nphoto = f"{photourl} " if photourl else ""
    nurl = (
        f"https://globe.airplanes.live/"
        f"?icao={icao}&showTrace={jsontoday}&zoom=7&timestamp={jsontimestamp} "
    )

    # Glue the bits together and it's ready to go
    notification = (
        f"{nplanetype}{noperator}{nicao}{nregistration}"
        f"{nflight}{nphoto}{nurl}#planealert"
    )

    print(notification)

    notify_url = os.environ.get(
        "UPA_NOTIFY_URL", "ntfy://upaunconfigured/?priority=min"
    )

    # This allows the use of an Idempotency key if configured
    # for mastodon.
    if "ICAOKEY" in notify_url:
        notify_url = notify_url.replace("ICAOKEY", icao)

    apobj = apprise.Apprise()
    apobj.add(notify_url)
    apobj.notify(
        body=notification,
    )


def main():
    build_database()
    print("Sleeping 60 seconds for ultrafeeder start-up")
    json_url = os.environ.get("UPA_JSON_URL", "http://ultrafeeder/data/aircraft.json")
    time.sleep(60)
    while 1:
        start_time = time.perf_counter()
        poll_planes(json_url)
        stop_time = time.perf_counter()
        loop_time = round(stop_time - start_time, 4)
        print(f"Loop complete in {loop_time} seconds, sleeping 90 seconds")
        time.sleep(90)


if __name__ == "__main__":
    main()
