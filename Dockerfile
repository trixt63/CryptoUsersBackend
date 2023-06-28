FROM python:3.9

WORKDIR /centic-api

COPY . /centic-api

RUN pip3 install web3==5.31.1 QueryStateLib==1.1.4
RUN pip3 install -r requirements.txt

CMD python3 /centic-api/main.py
