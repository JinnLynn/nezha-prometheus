FROM jinnlynn/uwsgi:py3.12

COPY app.py requirements.txt /app/opt/

RUN set -ex && \
    pip install -r /app/opt/requirements.txt

WORKDIR /app/opt/
