FROM python:3.10
WORKDIR /app
RUN apt-get update && apt-get install -y git
COPY . /app
RUN pip install -r requirements.txt