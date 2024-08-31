# micromaba
FROM ghcr.io/mamba-org/micromamba:latest@sha256:5ca96c708533dc7b1d6332dcabcbf74d7adfde56b7a822d94b27eae58a6e2e07
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
COPY --chown=$MAMBA_USER:$MAMBA_USER requirements.txt /tmp/requirements.txt
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
COPY upa.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/upa.py" ]
