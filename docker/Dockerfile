FROM python:3.7-alpine

ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-8294}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}
ARG NUM_THREADS
ENV NUM_THREADS ${NUM_THREADS:-2}
ARG WSGI_CONTAINER
ENV WSGI_CONTAINER ${WSGI_CONTAINER:-gunicorn}

COPY whls/*.whl /whls/

RUN addgroup -S kubedriver \
 && adduser -S kubedriver -G kubedriver -u 100 \
 && mkdir -p /var/kubedriver \
 && chown -R kubedriver:kubedriver /var/kubedriver \
 && apk add --no-cache bash binutils libc-dev \
 # These packages need to be installed so that we can install the Python dependencies.
 # We make this virtual so that we can remove them later
 && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git \
 && for i in /whls/ignition*.whl; do if [ "$i" != "/whls/ignition*.whl" ]; then pip install --no-warn-script-location --user "$i"; fi done \
 && for i in /whls/*.whl; do pip install "$i"; done \
 && apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

COPY helm2.8.2 /usr/local/bin/helm2.8.2
COPY helm2.11.0 /usr/local/bin/helm2.11.0

RUN helm2.8.2 --help

RUN helm2.11.0 --help

USER kubedriver
WORKDIR /home/kubedriver

EXPOSE 8294

CMD ["kubedriver"]