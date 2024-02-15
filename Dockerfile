FROM python:slim
RUN pip install --no-cache-dir apprise==1.7.2 orjson==3.9.14

VOLUME ["/app"]
WORKDIR /app
COPY upa.py /app
CMD ["python","-u","/app/upa.py"]
