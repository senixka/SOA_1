FROM python:3.9

COPY . /app

RUN apt-get update && apt-get install -y netcat
RUN pip3 install -r /app/requirements.txt

CMD ["python3", "/app/udp_server.py"]
