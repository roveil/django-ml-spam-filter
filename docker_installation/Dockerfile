FROM tensorflow/tensorflow:nightly-py3

# Define labels
ARG APP_HTTP_PORT
ARG BUILD_DATE
ARG MAINTAINER_LABEL
ARG VCS_REF
ARG VCS_URL_LABEL
ARG VENDOR_LABEL

LABEL \
  org.label-schema.build-date="${BUILD_DATE:-Now}" \
  org.label-schema.maintainer="${MAINTAINER_LABEL}" \
  org.label-schema.schema-version="1.0.0-rc1" \
  org.label-schema.vcs-ref="${VCS_REF}" \
  org.label-schema.vcs-url="${VCS_URL_LABEL}" \
  org.label-schema.vendor="${VENDOR_LABEL}" \
  org.label-schema.version="${APP_TAG:-edge}"

# Configure utf-8 locales to make sure Python
# correctly handles unicode filenames
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 DJANGO_SETTINGS_MODULE=django_ml_spam_filter.settings

# Add user early to get a consistent userid
RUN  addgroup --gid 1000 pyuser \
  && adduser -u 1000 --gid 1000 pyuser \
  && mkdir -p /app /app/svc /app/public \
  && chown -R pyuser:pyuser /app \
  && chmod 755 /app /app/svc /app/public \
  && echo 'Done.'

COPY --chown=pyuser:pyuser ./app /app/svc

# Install dependencies
RUN apt-get update \
  && apt-get install libpq-dev python3-dev \
  && pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir --upgrade --requirement /app/svc/requirements.txt \
  && python -m nltk.downloader punkt words wordnet averaged_perceptron_tagger \
  && echo 'Done.'

# Copy project dir with base config
COPY --chown=pyuser:pyuser ./private/config.container.py /app/svc/django_ml_spam_filter/config.py

USER pyuser
WORKDIR /app/svc

VOLUME [ "/app/public" ]

EXPOSE ${APP_HTTP_PORT}

# Dummy entrypoint & command with args
ENTRYPOINT [ "echo" ]
CMD [ "$@" ]
