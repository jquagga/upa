# Mostly from: https://github.com/GoogleContainerTools/distroless/blob/main/examples/python3-requirements/Dockerfile
# Build a virtualenv using the appropriate Debian release

FROM debian:12-slim@sha256:ccb33c3ac5b02588fc1d9e4fc09b952e433d0c54d8618d0ee1afadf1f3cf2455 AS build
COPY requirements.txt /requirements.txt
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    /venv/bin/pip install --no-cache-dir -r /requirements.txt

# Copy the virtualenv into a distroless image
FROM gcr.io/distroless/python3-debian12:nonroot@sha256:538f54b8d704c29137d337aeac1bfc874afd7db813b163b585366d57ec113e13
COPY --from=build /venv /venv
WORKDIR /app
COPY upa.py /app
ENTRYPOINT ["/venv/bin/python3","-u","/app/upa.py"]
