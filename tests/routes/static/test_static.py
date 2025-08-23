import os
from cat.utils import get_static_path

# TODOV2: the static folder should be mocked
# TODOV2: should the static folder be open or protected? (at the moment open)


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


    from cat.log import log
    log.critical(get_static_path())
    for r in client.app.routes:
        if r.path == '/static':
            log.warning(r.app.directory)

    response = client.get(f"/static/{static_file_name}")
    assert response.status_code == 200 # TODOV2: should this be 403?

