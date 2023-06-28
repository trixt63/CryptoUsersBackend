from sanic import Blueprint
from sanic import json
from sanic_ext import openapi, validate

from app.models.entity.relationship import RelationshipQuery

relationships_bp = Blueprint('relationships_blueprint', url_prefix='/relationships')


@relationships_bp.get('/')
@openapi.tag("Relationship")
@openapi.summary("Get relationship information")
@openapi.parameter(name="chain", description="Chain ID", schema=str, location="query")
@openapi.parameter(name="type", description="Relationship type", schema=str, location="query", required=True)
@openapi.parameter(name="fromNode", description="From node ID", schema=str, location="query", required=True)
@openapi.parameter(name="toNode", description="To node ID", schema=str, location="query", required=True)
@validate(query=RelationshipQuery)
async def get_relationship(request, query: RelationshipQuery):
    chain_id = query.chain

    data = {
        "source": {
            "id": "0x0c9fdcedee89a202d02e8a22a47fd772bc233bea",
            "type": "wallet",
            "name": "0x0c9...3bea",
            "address": "0x0c9fdcedee89a202d02e8a22a47fd772bc233bea"
        },
        "target": {
            "id": "0x53fec1f03b71aa84bd5b9ff9272435cd2ce0cf3b",
            "type": "wallet",
            "name": "0x53f...cf3b",
            "address": "0x53fec1f03b71aa84bd5b9ff9272435cd2ce0cf3b"
        },
        "type": "transfer"
    }
    
    return json(data)
