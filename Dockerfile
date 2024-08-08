FROM python:3.10.9

# FROM apache/airflow:slim-2.9.3

# USER root

# # Create user 'k9care'
# RUN useradd -ms /bin/bash k9care && \
#     chown -R k9care:k9care /opt/airflow

# USER k9care

RUN apk update \
  && apk add \
    build-base \
    postgresql \
    postgresql-dev \
    libpq

RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt .
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED 1

COPY . .