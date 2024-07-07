# micromaba
FROM ghcr.io/mamba-org/micromamba:latest@sha256:2efd90170dec2a9e7e4ea1ae1aa6dcdcb0e8458fdbba7708e65c1bf6c7d6c394
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
COPY --chown=$MAMBA_USER:$MAMBA_USER requirements.txt /tmp/requirements.txt
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
COPY upa.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/upa.py" ]
