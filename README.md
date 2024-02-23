# μPlaneAlert - microPlaneAlert

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/jquagga/upa/badge)](https://securityscorecards.dev/viewer/?uri=github.com/jquagga/upa)

μPlaneAlert is small python file which polls a tar1090 instance to report on interesting planes seen by a SDR. This is a subset of the functionality provided by [docker-planefence](https://github.com/sdr-enthusiasts/docker-planefence) written by Ramon F. Kolb. It's intended to run entirely in RAM and sleep between 90 second runs. It's one file, one process. Less functionally but easier on systems with less resources.

## Installation

Traditionally you would run upa in the docker-compose.yml stack along with ultrafeeder. It's default configuration is set to directly access the ultrafeeder container and read aircraft data, however that is configurable and it can run anywhere that has access to the aircraft.json file.

```yaml
services:
  ultrafeeder: <etc>
  upa:
    image: ghcr.io/jquagga/upa:main
    container_name: upa
    hostname: upa
    restart: unless-stopped
    environment:
      - UPA_NOTIFY_URL=mastodons://API_KEY@airwaves.social?visibility=unlisted
```

## Configuration

upa is configured entirely by environmental variables.

```
- UPA_NOTIFY_URL - An apprise URL stating where to post planealert notifications.
  It can be comma separated so you can message multiple services at once.

- UPA_PADATABASE_URL - The URL of interesting planes to send alerts on.
  By default, this is the SDR Enthusiasts list (same as planefence proper).
- UPA_JSON_URL - URL to the aircraft.json provided by tar1090.
  By default it will work if upa is running in the same network as ultrafeeder.
```

### Additional optional configuration

upa polls data from tar1090 and there are two settings which increase the amount of information it can provide. ENABLE_AC_DB defaults to on I believe, however the addition of --db-file-lt will allow upa to get "long form" plane descriptions. Think "AIRBUS A320-Neo" instead of "A32N". However if you like the short form, omitting this (but including the enable AC_DB) should allow that.

```yaml
services:
  ultrafeeder:
    environment:
      - TAR1090_ENABLE_AC_DB=true
      - READSB_EXTRA_ARGS=--db-file-lt
```

## Contributing

Pull requests are welcome! However we are still very much in the build phase so, I'm substantially changing things between updates. Once it settle's down then it may make more sense.

I'm probably going to resist feature creep as this was always supposed to be a basic shell. However it's really easy to fork this repo, have github build docker images (take a look in the .github folder) and change your docker-compose to utilize those images. Less configuration and "just run".

## Credits

- [Ramon F. Kolb](https://github.com/sdr-enthusiasts/docker-planefence) and docker-planefence are the basis for which this code is based on.
- [wreadsb/tar1090/](https://github.com/wiedehopf/readsb) is the core of everything upa is producing. It is the upstream data source.
- [SDR Enthusiasts](https://github.com/sdr-enthusiasts) maintain a dozen useful images for adsb, acars, and other radio related projects.
- [Apprise](https://github.com/caronc/apprise) powers the notification system. Drop the notification to the apprise url and it handles it from there. upa wouldn't do what it does without it.
