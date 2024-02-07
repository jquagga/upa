#!/usr/bin/python

import csv
import datetime
import io
import json
import os
import sqlite3
import time

import apprise
import requests

# Download and build database
# First lets fetch the csvfile and get it into shape
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
# Now let's build the sqlite db
connection = sqlite3.connect(":memory:")
cursor = connection.cursor()
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
connection.commit()

# Poll file, evaluate, notify and sleep 5 mins, repeat
json_url = os.environ.get("UPA_JSON_URL", "http://ultrafeeder/data/aircraft.json")
notify_url = os.environ.get("UPA_NOTIFY_URL", "ntfy://upaunconfigured/?priority=min")
print("Database complete, waiting 60 seconds for ultrafeeder start-up")
time.sleep(
    60
)  # Take a 60 second nap while first starting up to give ultrafeeder time to start
while 1:
    print("Starting a polling loop")
    response = requests.get(json_url, timeout=5)
    adsbdata = json.loads(response.text)
    # Build timestamp and date from json file for eventual notification URL
    jsontimestamp = int(adsbdata["now"])
    jsontoday = datetime.datetime.fromtimestamp(jsontimestamp, datetime.UTC).strftime(
        "%Y-%m-%d"
    )
    twohoursago = jsontimestamp - 7200
    # The json file format is a nest of all of the planes under 'aircraft'
    # So we need to loop through each entity in aircraft
    for plane in adsbdata["aircraft"]:
        # json is all lowercase, CSV file is all upcase so lets match.
        icao = plane["hex"].upper()
        planealert = cursor.execute(
            "SELECT * FROM planes WHERE icao=? AND lastseen<?",
            (icao, twohoursago),
        ).fetchall()
        if planealert:
            # Unbox the SQL data fields into registration, operator, etc
            # Unbox the json data fields into registration, operator, etc
            # FIXME: This needs to be a function since upf will do the same thing.
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
                planetype = plane["desc"].strip()
            elif "t" in plane.keys():
                planetype = plane["t"].upper().strip()
            else:
                planetype = ""

            if "flight" in plane.keys():
                flight = (
                    plane["flight"].upper().strip()
                )  # Flight number from json data if it's there.
            else:
                flight = ""

            # Notify
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
            apobj = apprise.Apprise()
            apobj.add(notify_url)
            apobj.notify(
                body=notification,
            )
            # This sets the lastseen time to now() in unix time.
            # Used for the 2 hour cooldown.
            cursor.execute(
                "UPDATE planes set lastseen=? WHERE icao=?",
                (jsontimestamp, icao),
            )
            connection.commit()
    print("Loop complete, sleeping 90 seconds")
    time.sleep(90)
