import time

import pytest
from sanic_testing.reusable import ReusableClient

from tests.parameters import AuthParams
from tests.utils.common_utils import assert_success_response


@pytest.mark.parametrize(AuthParams.names, [AuthParams.values])
def test_login(app, address, signature, nonce):
    client = ReusableClient(app)

    with client:
        # Login
        payload = {
            "address": address,
            "nonce": nonce,
            "signature": signature
        }
        _, response = client.post("/auth/login", json=payload)
        resp = assert_success_response(response)
        assert resp.get('jwt')
        assert resp['role'] in ['user', 'admin']

        # Check user
        jwt = resp.get('jwt')
        _, response = client.get(f"/auth/check-user?jwt={jwt}")
        resp = assert_success_response(response)
        assert resp['address'] == address.lower()
        assert resp['role'] in ['user', 'admin']
        assert isinstance(resp.get('exp'), int)
        assert resp.get('exp') > int(time.time())
