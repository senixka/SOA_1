FROM python:3.9

COPY udp_proxy.py /app/

RUN apt-get update && apt-get install -y netcat
RUN pip3 install flask==2.2.3

CMD ["python3", "/app/udp_proxy.py"]
