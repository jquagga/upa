# micromaba
FROM ghcr.io/mamba-org/micromamba:latest@sha256:56a397989b86966843604813076619204d79fd82dacac4eed0e34a251952fc1b
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
COPY --chown=$MAMBA_USER:$MAMBA_USER requirements.txt /tmp/requirements.txt
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
COPY upa.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/upa.py" ]
