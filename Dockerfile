FROM alpine:latest
MAINTAINER Bill Shetti "billshetti@gmail.com"
WORKDIR /app
ADD . /app

ENV REDIS_HOST="localhost"
ENV REDIS_PORT="6379"
ENV TRACER_HOST="localhost"
ENV TRACER_PORT="6832"


RUN apk update && \
    apk add python3 && \
    apk add python3-dev && \
    apk add py-pip && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
#    pip install --upgrade pip \
#    pip3 install setuptools \
    apk add py-flask && \
    apk add py-redis && \
    apk add py-requests && \
    apk add redis && \
    pip3 install redis_opentracing && \
    rm -rf /var/cache/* \
    rm -rf /root/.cache/*


COPY entrypoint/docker-entrypoint.sh /usr/local/bin/
RUN chmod 777 /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh /app # backwards compat

COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
EXPOSE 80
EXPOSE 5000
ENTRYPOINT ["docker-entrypoint.sh"]
#CMD ["python3", "cart.py"]
