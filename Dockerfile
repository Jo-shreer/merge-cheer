FROM python:3.13-alpine
COPY src/celebrate.py /pipe/celebrate.py
ENV ACTION_PATH=/pipe
ENTRYPOINT ["python3", "/pipe/celebrate.py"]
