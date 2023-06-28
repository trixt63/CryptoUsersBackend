import pytest
from sanic_testing.reusable import ReusableClient

from app.constants.network_constants import Chain
from tests.parameters import SearchTransactionParams, SearchBlockParams
from tests.utils.common_utils import assert_success_response


@pytest.mark.parametrize(SearchTransactionParams.names, [SearchTransactionParams.values])
def test_search_tx(app, tx_hash):
    client = ReusableClient(app)

    with client:
        # Search
        _, response = client.get(f"/explorer/search?keyword={tx_hash}")
        resp = assert_success_response(response)
        assert resp['keyword'] == tx_hash.lower()
        assert len(resp['results']) >= 1

        result = resp['results'][0]
        assert result.get('id')
        assert result.get('type') == 'transaction'
        assert result.get('name')
        assert len(result.get('chains', [])) == 1
        assert result['chains'][0] in Chain.chain_names


@pytest.mark.parametrize(SearchBlockParams.names, SearchBlockParams.values)
def test_search_block(app, block):
    client = ReusableClient(app)

    with client:
        # Search
        _, response = client.get(f"/explorer/search?keyword={block}")
        resp = assert_success_response(response)
        assert resp['keyword'] == block.lower()
        assert len(resp['results']) >= 1

        result = resp['results'][0]
        assert result.get('id')
        assert result.get('type') == 'block'
        assert result.get('name')
        assert len(result.get('chains', [])) == 1
        assert result['chains'][0] in Chain.chain_names
