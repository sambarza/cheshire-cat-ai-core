
# utility to retrieve embedded tools from endpoint
def get_procedural_memory_contents(client):
    params = {"text": "random"}
    response = client.get("/memory/recall/", params=params)
    json = response.json()
    return json["vectors"]["collections"]["procedural"]


# utility to retrieve declarative memory contents
def get_declarative_memory_contents(client):
    params = {"text": "Something"}
    response = client.get("/memory/recall/", params=params)
    assert response.status_code == 200
    json = response.json()
    declarative_memories = json["vectors"]["collections"]["declarative"]
    return declarative_memories


# utility to get collections and point count from `GET /memory/collections` in a simpler format
def get_collections_names_and_point_count(client):
    response = client.get("/memory/collections")
    json = response.json()
    assert response.status_code == 200
    collections_n_points = {c["name"]: c["vectors_count"] for c in json["collections"]}
    return collections_n_points