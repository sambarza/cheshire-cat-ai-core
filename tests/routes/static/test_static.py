import os
from cat.utils import get_static_path


def test_call(client):
    response = client.get("/static/")
    assert response.status_code == 404


def test_call_specific_file(client):
    static_file_name = "Meooow.txt"
    static_file_path = os.path.join(get_static_path(), static_file_name)

    # ask for inexistent file
    response = client.get(f"/static/{static_file_name}")
    assert response.status_code == 404

    # insert file in static folder
    with open(static_file_path, "w") as f:
        f.write("Meow")

    response = client.get(f"/static/{static_file_name}")
    assert response.status_code == 200 # TODOV2: should this be 403?

