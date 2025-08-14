import time
from tests.utils import send_websocket_message, send_n_websocket_messages


def check_correct_websocket_reply(reply):
    for k in ["type", "content", "user_id"]:
        assert k in reply.keys()

    assert reply["type"] != "error"
    assert isinstance(reply["content"], str)
    assert "You did not configure" in reply["content"]



def test_websocket_no_connections(client):

    # no ws 
    assert client.app.state.websocket_manager.connections == {}


def test_websocket(client):
    
    # send websocket message
    res = send_websocket_message({"text": "It's late! It's late"}, client)

    check_correct_websocket_reply(res)

    # websocket connection is closed
    time.sleep(0.5)
    assert client.app.state.websocket_manager.connections == {}


def test_websocket_multiple_messages(client):
    # send websocket message
    replies = send_n_websocket_messages(3, client)

    for res in replies:
        check_correct_websocket_reply(res)

    # websocket connection is closed
    time.sleep(0.5)
    assert client.app.state.websocket_manager.connections == {}


def test_websocket_multiple_connections(client):

    mex = {"text": "It's late!"}

    with client.websocket_connect("/ws/Alice") as websocket:

        # send ws message
        websocket.send_json(mex)

        with client.websocket_connect("/ws/Caterpillar") as websocket2:

            # send ws message
            websocket2.send_json(mex)
            # get reply
            reply2 = websocket2.receive_json()

            # two connections open
            ws_users = client.app.state.websocket_manager.connections.keys()
            assert set(ws_users) == {"Alice", "Caterpillar"}

        # one connection open
        time.sleep(0.5)
        ws_users = client.app.state.websocket_manager.connections.keys()
        assert set(ws_users) == {"Alice"}

        # get reply
        reply = websocket.receive_json()

    check_correct_websocket_reply(reply)
    check_correct_websocket_reply(reply2)

    # websocket connection is closed
    time.sleep(0.5)
    assert client.app.state.websocket_manager.connections == {}






