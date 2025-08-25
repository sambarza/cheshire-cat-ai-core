import shutil
from cat.convo.messages import ChatRequest, Message, MessageContent
from urllib.parse import urlencode


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
        "hooks": 10,
        "unique_hooks": 7,
        "tools": 1,
        "endpoints": 10,
        "forms": 0
    }


def get_mock_plugin_info():
    return {
        "id": "mock_plugin",
        "hooks": 4,
        "tools": 1,
        "forms": 1,
        "endpoints": 7
    }


def get_chat_request(msg="meow"):
    return ChatRequest(
        messages=[
            Message(
                role="user",
                content=MessageContent(
                    type="text",
                    text=msg
                )
            )
        ],
        stream=False
    )

def send_http_message(
        msg,
        client,
        streaming=False,
        headers={}
    ):
    res = client.post(
        "/chat",
        headers=headers,
        json={
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": str(msg)
                    }
                }
            ],
            "stream": streaming # TODOV2: should test streaming
        }
    )

    assert res.status_code == 200
    return res.json()        
        


# utility function to communicate with the cat via websocket
def send_websocket_message(msg, client, user_id="user", query_params=None):
    url = f"/ws/{user_id}"
    if query_params:
        url += "?" + urlencode(query_params)

    with client.websocket_connect(url) as websocket:

        # send ws message
        websocket.send_json({"text": str(msg)})
        # get reply
        reply = websocket.receive_json()

    return reply


# utility to send n messages via chat
def send_n_websocket_messages(num_messages, client, query_params=None):
    responses = []

    url = "/ws"
    if query_params:
        url += "?" + urlencode(query_params)

    with client.websocket_connect(url) as websocket:
        for m in range(num_messages):
            message = {"text": f"Red Queen {m}"}
            # sed ws message
            websocket.send_json(message)
            # get reply
            reply = websocket.receive_json()
            responses.append(reply)

    return responses


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


def create_new_user(client, admin_headers):
    new_user = {"username": "Alice", "password": "wandering_in_wonderland"}
    response = client.post("/users", headers=admin_headers, json=new_user)
    assert response.status_code == 200
    return response.json()
