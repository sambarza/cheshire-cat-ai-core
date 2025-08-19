from tests.utils import get_core_plugins_ids

def test_list_plugins(client):
    response = client.get("/plugins")
    json = response.json()

    assert response.status_code == 200
    for key in ["filters", "installed", "registry"]:
        assert key in json.keys()

    # query
    for key in ["query"]:  # ["query", "author", "tag"]:
        assert key in json["filters"].keys()

    # installed plugins
    for p in json["installed"]:
        assert p["id"] in get_core_plugins_ids()
        assert isinstance(p["active"], bool)
        assert p["active"]

    # registry (see more registry tests in `./test_plugins_registry.py`)
    assert isinstance(json["registry"], list)
    assert len(json["registry"]) > 0


def test_get_plugin_id(client):
    response = client.get("/plugins/qdrant_vector_memory") # one of the core plugins

    json = response.json()

    assert "data" in json.keys()
    assert json["data"] is not None
    assert json["data"]["id"] == "qdrant_vector_memory"
    assert isinstance(json["data"]["active"], bool)
    assert json["data"]["active"]


def test_get_non_existent_plugin(client):
    response = client.get("/plugins/no_plugin")
    json = response.json()

    assert response.status_code == 404
    assert json["detail"]["error"] == "Plugin not found"
