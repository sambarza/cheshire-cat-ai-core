
def test_http_message(client):
    
    response = client.post("/message", json={"text": "hello!"})

    assert response.status_code == 200
    assert "You did not configure" in response.json()["text"]