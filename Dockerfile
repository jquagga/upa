FROM python:slim@sha256:5c73034c2bc151596ee0f1335610735162ee2b148816710706afec4757ad5b1e
RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/app"]
WORKDIR /app
COPY upa.py /app
CMD ["python","-u","/app/upa.py"]
