
from tests.utils import send_http_message

def test_ping_success(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "We're all mad here, dear!"


def test_http_message(client):

    response = send_http_message("hello!", client)
    assert "You did not configure" in response["text"]