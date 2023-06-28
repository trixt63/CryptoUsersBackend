import pytest
from sanic_testing.reusable import ReusableClient

from tests.parameters import BlockParams
from tests.utils.common_utils import assert_success_response


@pytest.mark.parametrize(BlockParams.names, [BlockParams.values])
def test_block_intro(app, block_id):
    client = ReusableClient(app)

    with client:
        _, response = client.get(f"/blocks/{block_id}/introduction")
        resp = assert_success_response(response)
        assert resp['id'] == block_id

        allowable_keys = ['name', 'number', 'hash', 'explorerUrls', 'chains']
        for key in allowable_keys:
            assert key in resp

        assert len(resp.get('explorerUrls')) == 1
        assert len(resp.get('chains')) == 1


@pytest.mark.parametrize(BlockParams.names, [BlockParams.values])
def test_block_overview(app, block_id):
    client = ReusableClient(app)

    with client:
        _, response = client.get(f"/blocks/{block_id}/overview")
        resp = assert_success_response(response)
        assert resp['id'] == block_id

        allowable_keys = [
            'chain', 'hash', 'number', 'timestamp', 'numberOfTransactions', 'difficulty', 'totalDifficulty',
            'size', 'gasUsed', 'gasLimit', 'explorerUrl', 'validatedBy'
        ]
        for key in allowable_keys:
            assert key in resp


@pytest.mark.parametrize(BlockParams.names, [BlockParams.values])
def test_block_transactions(app, block_id):
    client = ReusableClient(app)

    with client:
        _, response = client.get(f"/blocks/{block_id}/transactions")
        resp = assert_success_response(response)
        assert resp['id'] == block_id

        allowable_keys = ['numberOfTransactions', 'transactions']
        for key in allowable_keys:
            assert key in resp

        assert resp['numberOfTransactions'] > 0
        assert 0 < len(resp['transactions']) <= resp['numberOfTransactions']

        for transaction in resp['transactions']:
            transaction_allowable_keys = [
                'id', 'chain', 'hash', 'blockNumber', 'timestamp',
                'fromAddress', 'toAddress', 'value', 'input', 'method', 'status'
            ]
            for key in transaction_allowable_keys:
                assert key in transaction

            for node_key in ['from', 'to']:
                if transaction.get(node_key):
                    node = transaction[node_key]
                    node_allowable_keys = ['id', 'address', 'name', 'type']
                    for key in node_allowable_keys:
                        assert key in node
                    assert node['type'] in ['wallet', 'token', 'contract']


@pytest.mark.parametrize(BlockParams.names, [BlockParams.values])
def test_block_visualize(app, block_id):
    client = ReusableClient(app)

    with client:
        _, response = client.get(f"/blocks/{block_id}/visualize")
        resp = assert_success_response(response)
        assert resp['id'] == block_id

        allowable_keys = ['nodes', 'links']
        for key in allowable_keys:
            assert key in resp

        nodes = resp.get('nodes')
        for node in nodes:
            node_allowable_keys = ['id', 'key', 'name', 'type']
            for key in node_allowable_keys:
                assert key in node

            assert node['type'] in ['wallet', 'token', 'contract', 'project']
            if node['type'] == 'project':
                assert 'metadata' in node
                assert 'projectType' in node['metadata']
                assert node['metadata']['projectType'] in ['defi', 'nft', 'exchange']

        nodes = {node['id']: node for node in nodes}
        links = resp.get('links')
        for link in links:
            link_allowable_keys = ['id', 'type', 'source', 'target']
            for key in link_allowable_keys:
                assert key in link

            assert link['source'] in nodes
            assert link['target'] in nodes
