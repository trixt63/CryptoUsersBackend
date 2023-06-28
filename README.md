![Logo](app/docs/images/logo-light.png)

# Centic API

API for Centic. Tracking and ranking all entities on Blockchain Space.

## Prerequisites
- Development
  - python 3.9
  - sanic >= 22.12.0
  - web3 == 5.31.1 & QueryStateLib == 1.1.4
  - redis: please make sure you have Redis instance running
- Production
  - docker 20.10.xx

## Setup variables environment

Copy `.env.example` file, then fill your config into the new `.env` file.
```shell
cp .env.example .env
```

## Local installation and development

Install dependencies
```shell
pip3 install web3==5.31.1 QueryStateLib==1.1.4
pip3 install -r requrements.txt
```

Run server with `python`
```shell
python3 main.py
```

or with `sanic`
```shell
sanic main.app -H 0.0.0.0 -p 8096 -w 4 -r
```

## Deployment
```shell
docker compose up
```

## Documentation
Access swagger document via [http://0.0.0.0:8096/docs](http://0.0.0.0:8096/docs)
