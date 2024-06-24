# micromaba
FROM ghcr.io/mamba-org/micromamba:latest@sha256:33d57a6e4edbb0d79ca699ce6456e291e86685181a720de646a9a21a82c9947e
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
COPY --chown=$MAMBA_USER:$MAMBA_USER requirements.txt /tmp/requirements.txt
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
COPY upa.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/upa.py" ]
