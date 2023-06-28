from sanic.exceptions import BadRequest


def wallet_transactions_with_pagination(query):
    if (not query.chain) and (query.page > 1):
        raise BadRequest('Chain ID must be set when page index is not the first.')
