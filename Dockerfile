FROM pypy:3
RUN pip install apprise requests

VOLUME ["/app"]
WORKDIR /app
COPY upa.py /app
CMD ["python","-u","/app/upa.py"]
