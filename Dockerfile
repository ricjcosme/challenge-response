FROM python:3.6.5-alpine3.7

WORKDIR /usr/src/app

RUN apk add --update \
  gcc \
  linux-headers \
  make \
  build-base \
  musl-dev \
  python-dev \
  && rm -rf /var/cache/apk/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python" ]
