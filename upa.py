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

# Poll file, evaluate, notify and sleep 5 mins #
json_url = os.environ.get("UPA_JSON_URL", "http://ultrafeeder/data/aircraft.json")
notify_url = os.environ.get("UPA_NOTIFY_URL", "ntfy://upaunconfigured/?priority=min")
while 1:
    response = requests.get(
        json_url, timeout=5
    )
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
        datapacket = cursor.execute(
            "SELECT * FROM planes WHERE icao=? AND lastseen<?",
            (icao, twohoursago),
        ).fetchall()
        if datapacket:
            # Unbox the SQL data fields into registration, operator, etc
            for info in datapacket:
                registration = info[1]
                operator = info[2].replace(
                    " ", "_"
                )  # Replace spaces with underscores to hashtags work.
                planetype = info[3]
                # if plane.get("flight"):
                #     flight = plane[
                #         "flight"
                #     ].upper()  # Flight number from json data if it's there.

            # Notify
            notification = (
                f"A {planetype} "
                f"operated by #{operator} "
                f"has been detected with ICAO #{icao}, "
                f"Registration #{registration} "
                #  f"operating Flight Number {flight}. "
                f"https://globe.airplanes.live/?icao={icao}&showTrace={jsontoday}&zoom=7&timestamp={jsontimestamp} "
                f"#planealert"
            )
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
    time.sleep(300)
