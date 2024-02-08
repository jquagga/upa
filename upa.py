#!/usr/bin/env python

"""upa.py: microplane alert. Checks sdr ultrafeeder output 
for interesting planes and issues notifications."""

import datetime
import io
import json
import os
import time

import apprise
import requests


def build_database():
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
    # Empty global dictionary to track lastseen for planefence
    global pfdb
    pfdb = {}


def poll_planes():
    print("Starting a polling loop")
    json_url = os.environ.get("UPA_JSON_URL", "http://ultrafeeder/data/aircraft.json")
    response = requests.get(json_url, timeout=5)
    adsbdata = json.loads(response.text)
    global jsontimestamp  # Needs to be global as it's not in the plane object
    jsontimestamp = int(adsbdata["now"])
    # The json file format is a nest of all of the planes under 'aircraft'
    # So we need to loop through each entity in aircraft
    for plane in adsbdata["aircraft"]:
        if planefence(plane):
            planerange = plane["r_dst"]
            notify(plane, planerange)
        elif planealert(plane):
            notify(plane, 0)

def planealert(plane):
    icao = plane["hex"].upper()
    twohoursago = jsontimestamp - 7200
    if icao not in padb.keys():
        return False
    if padb[icao] >= twohoursago:
        return False
    padb[icao] = jsontimestamp
    return True


def planefence(plane):
    if "r_dst" not in plane.keys():
        return False
    icao = plane["hex"].upper()
    twohoursago = jsontimestamp - 7200
    planerange = plane["r_dst"]
    if planerange > 2:
        return False
    if icao in pfdb.keys() and pfdb[icao] >= twohoursago:
        return False
    pfdb[icao] = jsontimestamp
    return True


def notify(plane, planerange):
    # If planerange is 0, it's a planealert; otherwise planefence
    icao = plane["hex"].upper()
    registration = (plane["r"].upper().strip()) if "r" in plane.keys() else ""
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
        planetype = ""

    flight = (plane["flight"].upper().strip()) if "flight" in plane.keys() else ""
    jsontoday = datetime.datetime.fromtimestamp(jsontimestamp, datetime.UTC).strftime(
        "%Y-%m-%d"
    )
    notification = (
        f"A {planetype} "
        f"operated by #{operator} "
        f"has been detected with ICAO #{icao}, "
        f"Registration #{registration} "
        f"operating Flight Number #{flight}. "
        f"https://radar.planespotters.net/?icao={icao}&showTrace={jsontoday}&zoom=7&timestamp={jsontimestamp} "
        f"#planealert"
    )
    print(notification)
    # If planerange is 0, this is planealert so go to that notification source
    # if not, go to the PF URL
    if planerange == 0:
        notify_url = os.environ.get(
            "UPA_NOTIFY_URL", "ntfy://upaunconfigured/?priority=min"
        )
    else:
        notify_url = os.environ.get("UPA_PF_URL", "dbus://")

    apobj = apprise.Apprise()
    apobj.add(notify_url)
    apobj.notify(
        body=notification,
    )


def main():
    build_database()
    print("Sleeping 60 seconds for ultrafeeder start-up")
    # time.sleep(60)
    while 1:
        poll_planes()
        print("Loop complete, sleeping 90 seconds")
        time.sleep(90)


if __name__ == "__main__":
    main()
