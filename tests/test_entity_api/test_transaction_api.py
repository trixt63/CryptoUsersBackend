import pytest
from sanic_testing.reusable import ReusableClient

from tests.parameters import TransactionParams
from tests.utils.common_utils import assert_success_response


@pytest.mark.parametrize(TransactionParams.names, [TransactionParams.values])
def test_tx_intro(app, tx_id):
    client = ReusableClient(app)

    with client:
        _, response = client.get(f"/transactions/{tx_id}/introduction")
        resp = assert_success_response(response)
        assert resp['id'] == tx_id

        allowable_keys = ['name', 'hash', 'explorerUrls', 'chains']
        for key in allowable_keys:
            assert key in resp

        assert len(resp.get('explorerUrls')) == 1
        assert len(resp.get('chains')) == 1


@pytest.mark.parametrize(TransactionParams.names, [TransactionParams.values])
def test_tx_overview(app, tx_id):
    client = ReusableClient(app)

    with client:
        _, response = client.get(f"/transactions/{tx_id}/overview")
        resp = assert_success_response(response)
        assert resp['id'] == tx_id

        allowable_keys = [
            'chain', 'hash', 'status', 'blockNumber', 'timestamp', 'fromAddress', 'toAddress', 'value',
            'method', 'input', 'gas', 'gasLimit', 'gasPrice', 'explorerUrl', 'fromAddressExplorerUrl', 'toAddressExplorerUrl'
        ]
        for key in allowable_keys:
            assert key in resp

        for node_key in ['from', 'to']:
            node = resp.get(node_key)
            node_allowable_keys = ['id', 'address', 'name', 'type']
            for key in node_allowable_keys:
                assert key in node
            assert node['type'] in ['wallet', 'token', 'contract']


@pytest.mark.parametrize(TransactionParams.names, [TransactionParams.values])
def test_tx_transfers(app, tx_id):
    client = ReusableClient(app)

    with client:
        _, response = client.get(f"/transactions/{tx_id}/transfers")
        resp = assert_success_response(response)
        assert resp['id'] == tx_id

        allowable_keys = ['numberOfTransfers', 'transfers']
        for key in allowable_keys:
            assert key in resp

        assert resp['numberOfTransfers'] > 0
        assert 0 < len(resp['transfers']) <= resp['numberOfTransfers']
        assert len(resp['transfers']) <= 20

        for transfer in resp['transfers']:
            transfer_allowable_keys = [
                'id', 'chain', 'transactionHash', 'blockNumber', 'timestamp',
                'fromAddress', 'toAddress', 'token', 'value'
            ]
            for key in transfer_allowable_keys:
                assert key in transfer

            for node_key in ['from', 'to']:
                if transfer.get(node_key):
                    node = transfer[node_key]
                    node_allowable_keys = ['id', 'address', 'name', 'type']
                    for key in node_allowable_keys:
                        assert key in node
                    assert node['type'] in ['wallet', 'token', 'contract']


@pytest.mark.parametrize(TransactionParams.names, [TransactionParams.values])
def test_tx_visualize(app, tx_id):
    client = ReusableClient(app)

    with client:
        _, response = client.get(f"/transactions/{tx_id}/visualize")
        resp = assert_success_response(response)
        assert resp['id'] == tx_id

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
