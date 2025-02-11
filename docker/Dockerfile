FROM python:3.10-alpine
RUN apk update && apk upgrade \
    && rm -rf /var/cache/apk/*

ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-8294}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}
ARG SUPPORTED_HELM_VERSIONS
ENV SUPPORTED_HELM_VERSIONS ${SUPPORTED_HELM_VERSIONS:-3.16.4}

COPY whls/*.whl /whls/

RUN addgroup -S kubedriver \
    && adduser -S kubedriver -G kubedriver -u 101 \
    && mkdir -p /var/kubedriver \
    # set group to 0 to allow arbitrary users in OCP to write to these directories
    && chown -R kubedriver:0 /var/kubedriver \
    && chmod -R 775 /var/kubedriver \
    && chown -R kubedriver:0 /home/kubedriver \
    && chmod -R 775 /home/kubedriver \
    && apk add --no-cache bash binutils libc-dev \
    # These packages need to be installed so that we can install the Python dependencies.
    # We make this virtual so that we can remove them later
    && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git \
    && for i in /whls/ignition*.whl; do if [ "$i" != "/whls/ignition*.whl" ]; then pip install --no-warn-script-location "$i"; fi done \
    && for i in /whls/*.whl; do pip install "$i"; done \
    && apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

COPY --chown=kubedriver:0 setup-helm.sh /setup-helm.sh 
RUN chmod +x /setup-helm.sh && sh /setup-helm.sh "$SUPPORTED_HELM_VERSIONS"

USER kubedriver
WORKDIR /home/kubedriver

EXPOSE 8294

CMD if [ $SSL_ENABLED | tr [:upper:] [:lower:] == "true" ]; then SSL="--certfile /var/kubedriver/certs/tls.crt --keyfile /var/kubedriver/certs/tls.key" ; fi \
    && gunicorn -k uvicorn.workers.UvicornWorker --workers $NUM_PROCESSES --bind [::]:$DRIVER_PORT $SSL "kubedriver:create_wsgi_app()"

