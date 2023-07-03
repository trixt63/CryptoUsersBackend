import random
import time

from sanic import Blueprint
from sanic import json
from sanic_ext import openapi, validate

from app.constants.time_constants import TimeConstants
from app.decorators.auth import protected
from app.models.portfolio.alerts import AlertsQuery

alerts_bp = Blueprint('alerts_blueprint', url_prefix='/')


@alerts_bp.get('/<address>/alerts')
@openapi.tag("Portfolio")
@openapi.summary("Get a list of notifications the wallet is alerted to.")
@openapi.parameter(name="type", description="Type of alerts (balance/token_price/dapp_apr).", schema=str, location="query")
@openapi.parameter(name="startTime", description="Start time to get notifications. Default: 24 hours ago.", schema=int, location="query")
@openapi.parameter(name="chain", description="Chain ID. If not set, return data in all chains.", schema=str, location="query")
@openapi.parameter(name="address", description="Wallet address", schema=str, location="path", required=True)
@openapi.secured('Authorization')
@protected
@validate(query=AlertsQuery)
async def get_dapps(request, address, query: AlertsQuery):
    chain_id = query.chain
    type_ = query.type
    startTime = query.startTime
    if startTime is None:
        startTime = int(time.time()) - TimeConstants.A_DAY

    # TODO: Calculate wallet alerts from startTime to current time
    # Filter by chain and type

    alerts = [
        {
            'timestamp': startTime + TimeConstants.A_HOUR + random.randint(0, TimeConstants.A_HOUR),
            'type': 'balance',
            'direct': 'increased',
            'valueInUSD': 3154,
            'changeRate': 0.144,
            'duration': TimeConstants.A_DAY
        },
        {
            'timestamp': startTime + random.randint(0, TimeConstants.A_HOUR),
            'type': 'token_price',
            'direct': 'decreased',
            'valueInUSD': 315,
            'changeRate': 0.44,
            'duration': TimeConstants.A_DAY,
            'token': {
                'id': 'trava-finance',
                'type': 'token',
                'name': 'Trava Finance',
                'symbol': 'TRAVA',
                'imgUrl': 'https://storage.googleapis.com/token-c515a.appspot.com/tokens_v2/TRAVA.png'

            }
        },
    ]

    return json({
        'address': address,
        'startTime': startTime,
        'endTime': int(time.time()),
        'alerts': alerts
    })
