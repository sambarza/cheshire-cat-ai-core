from json import dumps
from fastapi.encoders import jsonable_encoder
from cat.factory.embedder import get_embedders_schemas


def test_get_all_embedder_settings(client, admin_headers):
    EMBEDDER_SCHEMAS = get_embedders_schemas()
    response = client.get("/embedder/settings", headers=admin_headers)
    json = response.json()

    assert response.status_code == 200
    assert isinstance(json["settings"], list)
    assert len(json["settings"]) == len(EMBEDDER_SCHEMAS)

    for setting in json["settings"]:
        assert setting["name"] in EMBEDDER_SCHEMAS.keys()
        assert setting["value"] == {}
        expected_schema = EMBEDDER_SCHEMAS[setting["name"]]
        assert dumps(jsonable_encoder(expected_schema)) == dumps(setting["schema"])

    # selected embedder
    assert json["selected_configuration"] is None # no llm configured at startup


def test_get_embedder_settings_non_existent(client, admin_headers):
    non_existent_embedder_name = "EmbedderNonExistentConfig"
    response = client.get(
        f"/embedder/settings/{non_existent_embedder_name}",
        headers=admin_headers
    )
    json = response.json()

    assert response.status_code == 400
    assert f"{non_existent_embedder_name} not supported" in json["detail"]["error"]


def test_get_embedder_settings(client, admin_headers):
    embedder_name = "EmbedderDefaultConfig"
    response = client.get(
        f"/embedder/settings/{embedder_name}",
        headers=admin_headers
    )
    json = response.json()

    assert response.status_code == 200
    assert json["name"] == embedder_name
    assert json["value"] == {}  # Default Embedder has indeed an empty config (no options)
    assert json["schema"]["languageEmbedderName"] == embedder_name
    assert json["schema"]["type"] == "object"


def test_upsert_embedder_settings(client, admin_headers, just_installed_plugin):
    # set a different embedder from default one (same class different size # TODO: have another fake/test embedder class)
    new_embedder = "EmbedderTestConfig"
    embedder_config = {"size": 64}
    response = client.put(
        f"/embedder/settings/{new_embedder}",
        json=embedder_config,
        headers=admin_headers
    )
    json = response.json()

    # verify success
    assert response.status_code == 200
    assert json["name"] == new_embedder
    assert json["value"]["size"] == embedder_config["size"]

    # retrieve all embedders settings to check if it was saved in DB
    response = client.get("/embedder/settings", headers=admin_headers)
    json = response.json()
    assert response.status_code == 200
    assert json["selected_configuration"] == new_embedder
    saved_config = [c for c in json["settings"] if c["name"] == new_embedder]
    assert saved_config[0]["value"]["size"] == embedder_config["size"]

    # check also specific embedder endpoint
    response = client.get(f"/embedder/settings/{new_embedder}", headers=admin_headers)
    assert response.status_code == 200
    json = response.json()
    assert json["name"] == new_embedder
    assert json["value"]["size"] == embedder_config["size"]
    assert json["schema"]["languageEmbedderName"] == new_embedder

    # TODOV2: there should be an endpoint to produce the embeddings



