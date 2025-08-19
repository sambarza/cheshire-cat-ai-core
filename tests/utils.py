import os
import shutil
from urllib.parse import urlencode


def get_mock_plugins_path():
    """Plugins folder used just for testing"""
    path = os.path.join(os.getcwd(), "mock_plugins")
    os.makedirs(path, exist_ok=True)
    return path


def get_core_plugins_ids():
    return get_core_plugins_info()["ids"]


def get_core_plugins_info():
    return {
        "ids": {
            "base_tools",
            "langchain_models_pack",
            "legacy_v1",
            "model_interactions",
            "rabbit_hole",
            "qdrant_vector_memory",
            "white_rabbit",
            "why"
        },
        "hooks": 6, # + 2
        "unique_hooks": 5, # + ?
        "tools": 1,
        "endpoints": 10,
        "forms": 0
    }


def get_mock_plugin_info():
    return {
        "id": "mock_plugin",
        "hooks": 3,
        "tools": 1,
        "forms": 1,
        "endpoints": 7
    }


# utility function to communicate with the cat via websocket
def send_websocket_message(msg, client, user_id="user", query_params=None):
    url = f"/ws/{user_id}"
    if query_params:
        url += "?" + urlencode(query_params)

    with client.websocket_connect(url) as websocket:

        # send ws message
        websocket.send_json(msg)
        # get reply
        reply = websocket.receive_json()

    return reply


# utility to send n messages via chat
def send_n_websocket_messages(num_messages, client):
    responses = []

    with client.websocket_connect("/ws") as websocket:
        for m in range(num_messages):
            message = {"text": f"Red Queen {m}"}
            # sed ws message
            websocket.send_json(message)
            # get reply
            reply = websocket.receive_json()
            responses.append(reply)

    return responses


def key_in_json(key, json):
    return key in json.keys()


# create a plugin zip out of the mock plugin folder.
# - Used to test plugin upload.
# - zip can be created flat (plugin files in root dir) or nested (plugin files in zipped folder)
def create_mock_plugin_zip(flat: bool):
    if flat:
        root_dir = "tests/mocks/mock_plugin"
        base_dir = "./"
    else:
        root_dir = "tests/mocks/"
        base_dir = "mock_plugin"

    return shutil.make_archive(
        base_name="tests/mocks/mock_plugin",
        format="zip",
        root_dir=root_dir,
        base_dir=base_dir,
    )


def create_new_user(client):
    new_user = {"username": "Alice", "password": "wandering_in_wonderland"}
    response = client.post("/users", json=new_user)
    assert response.status_code == 200
    return response.json()
