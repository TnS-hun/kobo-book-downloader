FROM python:3.7-slim-buster

COPY . /home
WORKDIR /home
RUN pip3 install .
ENTRYPOINT ["kobodl"]
