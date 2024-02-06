# μPlaneAlert - microPlaneAlert

**This is new software and while it works for me, it isn't heavily tested, improved, etc yet!**

So μPlaneAlert is small python file attempting to do the basics planealert found in more full-featured [docker-planefence](https://github.com/sdr-enthusiasts/docker-planefence) written by Ramon F. Kolb. planealert in planefence works great, but I wanted something simpler and slightly different and this was also an excuse to learn some python.

## What it does

The docker image runs the solo python file. That downloads the [SDR Enthusiasts list of interesting planes](https://github.com/sdr-enthusiasts/plane-alert-db) as a CSV file and loads it into a memory sqlite database. It'll then poll an `airplanes.json` file from readsb / tar1090 but is really designed to run in the stack with the [ultrafeeder](https://github.com/sdr-enthusiasts/docker-adsb-ultrafeeder). If there is a ICAO code matching the interesting planes file, upa builds a notification and hands it off to [apprise](https://github.com/caronc/apprise) which can notify however many services you configure. I use it to post to mastodon but out of the box it sends notices to a ntfy.sh instance for testing. After the notification, it updates a column in the sqlite database for a 2 hour break before notifying again. Then it sleeps for 5 minutes and searches again.

## What it doesn't do

I only wanted the planealert functionality so upa doesn't do anything similar to planefence. It doesn't know where it is, the receiver is and it doesn't track where the plane is. All it knows is that the json file it was fed heard an interesting ICAO and posts about it. This also means it doesn't need to do as much math or need socket30003 data. The tar1090 json file has everything it needs.

## What it might do in the future

- Photos. upa wasn't built to use the photos in the plane-alert-db. While they're nice, I'm not sure about the license to repost them etc. It may be possible to use the planespotter api in the future to check for photos similar to what tar1090 does, but their terms of service don't allow reposting the photos to mastodon so I'd have to just link them. And they're already on the tar1090 page linked in the post so I'm not sure if I'll add this.
- Logging - presently there is none!
- Optimizations, functions, fun basic things like that.

## Running it

The python can be run essentially anywhere that has access to your tar1090 webserver so it doesn't have to run alongside the sdr-enthusiasts stack. However, for sheer simplicity, that's probably where I think most people would dump it. It is configured by 3 environmental variables and if you're using it in the ultrafeeder stack, you probably only need to configure `UPA_NOTIFY_URL`. This is a comma-separated list of apprise URLs so take a look at the [mastodon](https://github.com/caronc/apprise/wiki/Notify_mastodon) examples. But apprise will happily post to many services (although note the format is different that planefence, especially compared to their better discord notifications).
