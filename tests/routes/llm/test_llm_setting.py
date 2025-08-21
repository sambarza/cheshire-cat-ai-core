from json import dumps
from fastapi.encoders import jsonable_encoder
from cat.factory.llm import get_llms_schemas

from tests.utils import send_http_message


def test_get_all_llm_settings(client, admin_headers):
    llms_schemas = get_llms_schemas()

    response = client.get("/llm/settings", headers=admin_headers)
    json = response.json()

    assert response.status_code == 200
    assert isinstance(json["settings"], list)
    assert len(json["settings"]) == len(llms_schemas)

    for setting in json["settings"]:
        assert setting["name"] in llms_schemas.keys()
        assert setting["value"] == {}
        expected_schema = llms_schemas[setting["name"]]
        assert dumps(jsonable_encoder(expected_schema)) == dumps(setting["schema"])

    assert json["selected_configuration"] is None  # no llm configured at startup


def test_get_llm_settings_non_existent(client, admin_headers):
    non_existent_llm_name = "LLMNonExistentConfig"
    response = client.get(
        f"/llm/settings/{non_existent_llm_name}",
        headers=admin_headers
    )
    json = response.json()

    assert response.status_code == 400
    assert f"{non_existent_llm_name} not supported" in json["detail"]["error"]


def test_get_llm_settings(client, admin_headers):
    llm_name = "LLMDefaultConfig"
    response = client.get(f"/llm/settings/{llm_name}", headers=admin_headers)
    json = response.json()

    assert response.status_code == 200
    assert json["name"] == llm_name
    assert json["value"] == {}
    assert json["schema"]["languageModelName"] == llm_name
    assert json["schema"]["type"] == "object"


def test_upsert_llm_settings_success(client, just_installed_plugin, admin_headers):
    
    # set a different LLM
    new_llm = "TestLLMConfig"
    expected_responses = ["meow", "bao", "baobab"]
    payload = {"responses": expected_responses}
    response = client.put(f"/llm/settings/{new_llm}", headers=admin_headers, json=payload)

    # check immediate response
    json = response.json()
    assert response.status_code == 200
    assert json["name"] == new_llm
    assert json["value"]["responses"] == expected_responses

    # retrieve all LLMs settings to check if it was saved in DB
    response = client.get("/llm/settings", headers=admin_headers)
    json = response.json()
    assert response.status_code == 200
    assert json["selected_configuration"] == new_llm
    saved_config = [c for c in json["settings"] if c["name"] == new_llm]
    assert saved_config[0]["value"]["responses"] == expected_responses

    # check also specific LLM endpoint
    response = client.get(f"/llm/settings/{new_llm}", headers=admin_headers)
    assert response.status_code == 200
    json = response.json()
    assert json["name"] == new_llm
    assert json["value"]["responses"] == expected_responses
    assert json["schema"]["languageModelName"] == new_llm

    # check expected replies form test LLM
    for er in expected_responses:
        reply = send_http_message("meow", client, headers=admin_headers)
        assert reply["text"] == er