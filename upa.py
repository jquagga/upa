#!/usr/bin/env python

"""upa.py: microplane alert. Checks sdr ultrafeeder output 
for interesting planes and issues notifications."""

import csv
import datetime
import io
import json
import os
import sqlite3
import time

import apprise
import requests

# Database initialized globally to move between functions
sqldb = sqlite3.connect(":memory:")


def build_database():
    print("Downloading alert csv")
    database_url = os.environ.get(
        "UPA_PADATABASE_URL",
        "https://github.com/sdr-enthusiasts/plane-alert-db/raw/main/plane-alert-db.csv",
    )
    r = requests.get(
        database_url,
        timeout=5,
    )
    csvfile = io.StringIO(r.text)
    contents = csv.reader(csvfile)
    next(contents)  # Skip the header row in the csv file
    print("Building database")
    cursor = sqldb.cursor()
    cursor.execute(
        """
        CREATE TABLE planes (
        icao TEXT,
        registration TEXT,
        operator TEXT,
        type TEXT,
        icao_type TEXT,
        cmpg TEXT,
        tag1 TEXT,
        tag2 TEXT,
        tag3 TEXT,
        category TEXT,
        link TEXT
    )
    """
    )
    INSERT_RECORDS = "INSERT INTO planes (icao, registration, operator, type, icao_type, cmpg, tag1, tag2, tag3, category, link) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    # # This imports the "Stock csv into sqlite"
    cursor.executemany(INSERT_RECORDS, contents)
    # # And this adds a "lastseen column" at the end.
    cursor.execute("ALTER TABLE planes ADD COLUMN lastseen NOT NULL DEFAULT 0;")
    sqldb.commit()
    global pfdb
    pfdb = {}  # Empty global dictionary to track lastseen for planefence


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
            range = plane["r_dst"]
            notify(plane, range)
        elif planealert(plane):
            notify(plane, 0)


def planealert(plane):
    icao = plane["hex"].upper()
    twohoursago = jsontimestamp - 7200
    cursor = sqldb.cursor()
    papresent = cursor.execute(
        "SELECT * FROM planes WHERE icao=? AND lastseen<?",
        (icao, twohoursago),
    ).fetchall()
    if papresent:
        cursor.execute(
            "UPDATE planes set lastseen=? WHERE icao=?",
            (jsontimestamp, icao),
        )
        sqldb.commit()
        return 1
    else:
        return 0


def planefence(plane):
    # First check if the plane even has a range value. If not,
    # give up now.
    if "r_dst" in plane.keys():
        icao = plane["hex"].upper()
        twohoursago = jsontimestamp - 7200
        range = plane["r_dst"]
        # Walking through the if's in order
        # First, are we closer than 2 nmi?
        if range <= 2:
            # If we are closer, is this ICAO already in
            # the dictionary (ie, we've seen it before?)
            if icao in pfdb.keys():
                # If it is in the dictionary, has it been more than
                # 2 hours?  If so update lastseen and return 1
                if pfdb[icao] < twohoursago:
                    pfdb[icao] = jsontimestamp
                    return 1
                # If it hasn't been 2 hours, return 0.
                else:
                    return 0
            # If the icao isn't in the dictionary it's new!
            # so add its lastseen and return 1
            else:
                pfdb[icao] = jsontimestamp
                return 1
        # If range isn't 2, return 0
        else:
            return 0
    # And if we don't have a range figure at all, return 0
    else:
        return 0


def notify(plane, range):
    # If range is 0, it's a planealert; otherwise planefence
    icao = plane["hex"].upper()
    if "r" in plane.keys():
        registration = (
            plane["r"].upper().strip()
        )  # Plane Registration from json data if it's there.
    else:
        registration = ""
    if "ownOp" in plane.keys():
        operator = (
            plane["ownOp"].upper().strip().replace(" ", "_")
        )  # Replace spaces with underscores to hashtags work.
    else:
        operator = ""
    if "desc" in plane.keys():
        planetype = plane["desc"].strip()  # desc requires extended fields enabled
    elif "t" in plane.keys():
        planetype = plane["t"].upper().strip()  # if not, we fall back to t
    else:
        planetype = ""
    if "flight" in plane.keys():
        flight = (
            plane["flight"].upper().strip()
        )  # Flight number from json data if it's there.
    else:
        flight = ""
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
    notify_url = os.environ.get(
        "UPA_NOTIFY_URL", "ntfy://upaunconfigured/?priority=min"
    )
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
