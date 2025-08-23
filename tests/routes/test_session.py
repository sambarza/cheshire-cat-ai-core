# TODOV2: new tests for the session once the cat is statelessimport os
#import time
#import os
import pytest
from cat.memory.working_memory import WorkingMemory
#from cat.cache.cache_manager import CacheManager
#from cat.cache.in_memory_cache import InMemoryCache
#from cat.cache.file_system_cache import FileSystemCache

from tests.utils import send_websocket_message, send_http_message


# only valid for in_memory cache
def test_no_sessions_at_startup(client):

    for username in ["admin", "user", "Alice"]:
        wm = client.app.state.ccat.cache.get_value(f"{username}_working_memory")
        assert wm is None


@pytest.mark.parametrize("protocol", ["ws", "http"])
def test_session_creation(client, admin_headers, admin_query_params, protocol):

    # send message
    mex = "Where do I go?"
    if protocol == "ws":
        res = send_websocket_message(
            mex, client, user_id="Alice", query_params=admin_query_params
        )
    else:
        admin_headers["user_id"] = "Alice"
        res = send_http_message(mex, client, headers=admin_headers)

    # check response
    assert res["user_id"] == "Alice"
    assert "You did not configure" in res["text"]

    # verify session
    wm = client.app.state.ccat.cache.get_value("Alice_working_memory")
    assert isinstance(wm, WorkingMemory)


@pytest.mark.parametrize("protocol", ["ws", "http"])
def test_session_update(client, admin_headers, admin_query_params, protocol):

    for message in range(5):

        # send message
        if protocol == "ws":
            res = send_websocket_message(message, client, user_id="Caterpillar", query_params=admin_query_params)
        else:
            admin_headers["user_id"] = "Caterpillar"
            res = send_http_message(message, client, headers=admin_headers)

        # check response
        assert res["user_id"] == "Caterpillar"
        assert "You did not configure" in res["text"]

        # verify session
        wm = client.app.state.ccat.cache.get_value("Caterpillar_working_memory")
        assert isinstance(wm, WorkingMemory)

        assert False
        # TODOV2: what are the side effects on wm while we have no more messages in there?


# TODOV2: this test must be heavily updated
"""
@pytest.mark.parametrize("cache_type", ["in_memory", "file_system"])
def test_session_sync_between_protocols(client, cache_type):

    # change cache type (depends on env variables)
    os.environ["CCAT_CACHE_TYPE"] = cache_type
    client.app.state.ccat.cache = CacheManager().cache

    if cache_type == "file_system":
        assert isinstance(client.app.state.ccat.cache, FileSystemCache)
    elif cache_type == "in_memory":
        assert isinstance(client.app.state.ccat.cache, InMemoryCache)
    else:
        assert False

    for message in range(5):

        # send messages alternating between ws and http
        if message % 2 == 0:
            res = send_websocket_message(message, client, user_id="Caterpillar")
        else:
            res = client.post(
                "/chat",
                json=mex,
                headers={"user_id": "Caterpillar"}
            ).json()

        # check response
        assert res["user_id"] == "Caterpillar"
        assert "You did not configure" in res["text"]

        # verify session
        time.sleep(0.1) # give time to write file in case of file_system cache
        wm = client.app.state.ccat.cache.get_value("Caterpillar_working_memory")
        assert isinstance(wm, WorkingMemory)
        assert len(wm.history) == int(message + 1) * 2 # user mex + reply
        for c_idx, c in enumerate(wm.history):
            if c_idx % 2 == 0:
                assert c.who == "Human"
                assert c.text == str(c_idx // 2)
            else:
                assert c.who == "AI"
                assert "You did not configure" in c.text

    # restore default env variable for cache
    del os.environ["CCAT_CACHE_TYPE"]


def test_session_sync_while_websocket_is_open(client):

    mex = {"text": "Oh dear!"}

    # keep open a websocket connection
    with client.websocket_connect("/ws/Alice") as websocket:
        # send ws message
        websocket.send_json(mex)
        # get reply
        res = websocket.receive_json()

        # checks
        wm = client.app.state.ccat.cache.get_value("Alice_working_memory")
        assert res["user_id"] == "Alice"
        assert len(wm.history) == 2

        # send another mex via http while ws connection is open
        res = client.post(
            "/chat",
            json=mex,
            headers={"user_id": "Alice"}
        ).json()

        # checks
        assert res["user_id"] == "Alice"
        wm = client.app.state.ccat.cache.get_value("Alice_working_memory")
        assert len(wm.history) == 4

        # clear convo history via http while nw connection is open
        res = client.delete("/memory/conversation_history", headers={"user_id": "Alice"})
        # checks
        assert res.status_code == 200
        wm = client.app.state.ccat.cache.get_value("Alice_working_memory")
        assert len(wm.history) == 0

    # at connection closed, rerun checks
    time.sleep(0.5)
    wm = client.app.state.ccat.cache.get_value("Alice_working_memory")
    assert len(wm.history) == 0

@pytest.mark.parametrize("cache_type", ["in_memory", "file_system"])
def test_session_sync_when_websocket_gets_closed_and_reopened(client, cache_type):
    mex = {"text": "Oh dear!"}

    try:
        os.environ["CCAT_CACHE_TYPE"] = cache_type
        client.app.state.ccat.cache = CacheManager().cache

        # keep open a websocket connection
        with client.websocket_connect("/ws/Alice") as websocket:
            # send ws message
            websocket.send_json(mex)
            # get reply
            res = websocket.receive_json()

            # checks
            wm = client.app.state.ccat.cache.get_value("Alice_working_memory")
            assert res["user_id"] == "Alice"
            assert len(wm.history) == 2

            # clear convo history via http while nw connection is open
            res = client.delete("/memory/conversation_history", headers={"user_id": "Alice"})
            # checks
            assert res.status_code == 200
            wm = client.app.state.ccat.cache.get_value("Alice_working_memory")
            assert len(wm.history) == 0

        time.sleep(0.5)

        # at connection closed, reopen a new connection and rerun checks
        with client.websocket_connect("/ws/Alice") as websocket:
            wm = client.app.state.ccat.cache.get_value("Alice_working_memory")
            assert len(wm.history) == 0

    finally:
        del os.environ["CCAT_CACHE_TYPE"]



# in_memory cache can store max 100 sessions
def test_sessions_are_deleted_from_in_memory_cache(client):

    cache = client.app.state.ccat.cache
    mex = {"text": "Oh dear!"}

    for user_id in range(cache.max_items + 10):
        send_websocket_message(mex, client, user_id=str(user_id))
        assert len(cache.items) <= cache.max_items
"""



# TODOV2: how do we test that:
# - streaming happens

