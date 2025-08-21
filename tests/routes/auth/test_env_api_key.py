import os
import pytest
from tests.utils import send_websocket_message


# utility to make http requests with some headers
def http_request(client, headers={}):
    response = client.get("/status", headers=headers)
    return response.status_code, response.json()


def test_http_auth(client):

    wrong_headers = [
        {}, # no header
        { "Authorization": "" },
        { "Authorization": "meow" }, # no Bearer prefix
        { "Authorization": "Bearer wrong" }, # wrong key
    ]

    # all the previous headers result in a 403
    for headers in wrong_headers:
        status_code, json = http_request(client, headers)
        assert status_code == 403
        assert json["detail"]["error"] == "Invalid Credentials"

    # allow access if CCAT_API_KEY is right
    headers = {"Authorization": "Bearer meow"}
    status_code, json = http_request(client, headers)
    assert status_code == 200
    assert json["status"] == "We're all mad here, dear!"


def test_ws_auth(client):

    mex = {"text": "Where do I go?"}

    wrong_query_params = [
        None, # no key
        { "token": "wrong" }, # wrong key
    ]

    for params in wrong_query_params:
        with pytest.raises(Exception) as e_info:
            res = send_websocket_message(mex, client, query_params=params)
        assert str(e_info.type.__name__) == "WebSocketDisconnect"

    # allow access if CCAT_API_KEY is right
    query_params = {"token": "meow"}
    res = send_websocket_message(mex, client, query_params=query_params)
    assert "You did not configure" in res["content"]


def test_all_core_endpoints_secured(client):
    # using client fixture, so both http and ws keys are set

    open_endpoints = [
        "/openapi.json",
        "/auth/login",
        "/auth/token",
        "/auth/token-form",
        "/docs",
        "/docs/oauth2-redirect" # TODO: can this endpoint be avoided? it's added by OAuth scheme for the swagger
    ]

    # test all endpoints are secured
    for endpoint in client.app.routes:

        # websocket endpoint
        if "/ws" in endpoint.path:
            with pytest.raises(Exception) as e_info:
                send_websocket_message({"text": "Where do I go?"}, client)
                assert str(e_info.type.__name__) == "WebSocketDisconnect"
        # static admin files (redirect to login)
        elif "/admin" in endpoint.path:
            response = client.get(endpoint.path, follow_redirects=False)
            assert response.status_code == 307            
        # static files http endpoints (open)
        # TODOV2 static routes should be closed also
        elif "/static" in endpoint.path \
                or "/core-static" in endpoint.path:
            response = client.get(endpoint.path)
            assert response.status_code in {200, 404}
        # REST API http endpoints
        else:    
            for verb in endpoint.methods:
                response = client.request(verb, endpoint.path)

                from cat.log import log
                log.warning(endpoint.path)

                if endpoint.path in open_endpoints:
                    assert response.status_code in {200, 400}
                else:
                    assert response.status_code == 403
