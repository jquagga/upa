# micromaba
FROM ghcr.io/mamba-org/micromamba:latest@sha256:962a071da85a5be8dfe55e194c674f3bd1dab8ccbcc3c26d69b09a25439d9c30
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
COPY --chown=$MAMBA_USER:$MAMBA_USER requirements.txt /tmp/requirements.txt
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
COPY upa.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/upa.py" ]
