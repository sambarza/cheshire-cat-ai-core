from uuid import UUID
from cat.auth.permissions import get_base_permissions, get_full_permissions
from tests.utils import create_new_user


def check_user_fields(u):
    assert set(u.keys()) == {"id", "username", "permissions"}
    assert isinstance(u["username"], str)
    assert isinstance(u["permissions"], dict)
    try:
        # Attempt to create a UUID object from the string to validate it
        uuid_obj = UUID(u["id"], version=4)
        assert str(uuid_obj) == u["id"]
    except ValueError:
        # If a ValueError is raised, the UUID string is invalid
        assert False, "Not a UUID"

def test_create_user(client, admin_headers):

    # create user
    data = create_new_user(client, admin_headers)

    # assertions on user structure
    check_user_fields(data)

    assert data["username"] == "Alice"
    assert data["permissions"] == get_base_permissions()

def test_cannot_create_duplicate_user(client, admin_headers):

    # create user
    response = create_new_user(client, admin_headers)

    # create user with same username
    response = client.post(
        "/users",
        headers=admin_headers,
        json={"username": "Alice", "password": "ecilA"}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "Cannot duplicate user"

def test_get_users(client, admin_headers):

    # get list of users
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2 # admin and user

    # create user
    create_new_user(client, admin_headers)

    # get updated list of users
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3 # admin, user and Alice

    # check users integrity and values
    for idx, d in enumerate(data):
        check_user_fields(d)
        assert d["username"] in ["admin", "user", "Alice"]
        if d["username"] == "admin":
            assert d["permissions"] == get_full_permissions()
        else:
            assert d["permissions"] == get_base_permissions()

def test_get_user(client, admin_headers):

    # get unexisting user
    response = client.get("/users/wrong_user_id", headers=admin_headers)
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "User not found"

    # create user and obtain id
    user_id = create_new_user(client, admin_headers)["id"]

    # get specific existing user
    response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()

    # check user integrity and values
    check_user_fields(data)
    assert data["username"] == "Alice"
    assert data["permissions"] == get_base_permissions()

def test_update_user(client, admin_headers):

    # update unexisting user
    response = client.put(
        "/users/non_existent_id",
        headers=admin_headers,
        json={"username": "Red Queen"}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "User not found"

    # create user and obtain id
    user_id = create_new_user(client, admin_headers)["id"]

    # update unexisting attribute (bad request)
    updated_user = {"username": "Alice", "something": 42}
    response = client.put(f"/users/{user_id}", headers=admin_headers, json=updated_user)
    assert response.status_code == 400

    # change nothing
    response = client.put(f"/users/{user_id}", headers=admin_headers, json={})
    assert response.status_code == 200
    data = response.json()

    # nothing changed so far
    check_user_fields(data)
    assert data["username"] == "Alice"
    assert data["permissions"] == get_base_permissions()
    
    # update password
    updated_user = {"password": "12345"}
    response = client.put(f"/users/{user_id}", headers=admin_headers, json=updated_user)
    assert response.status_code == 200
    data = response.json()
    check_user_fields(data)
    assert data["username"] == "Alice"
    assert data["permissions"] == get_base_permissions()
    assert "password" not in data # api will not send passwords around
    
    # change username
    updated_user = {"username": "Alice2"}
    response = client.put(f"/users/{user_id}", headers=admin_headers, json=updated_user)
    assert response.status_code == 200
    data = response.json()
    check_user_fields(data)
    assert data["username"] == "Alice2"
    assert data["permissions"] == get_base_permissions()

    # change permissions
    updated_user = {"permissions": {"MEMORY": ["READ"]}}
    response = client.put(f"/users/{user_id}", headers=admin_headers, json=updated_user)
    assert response.status_code == 200
    data = response.json()
    check_user_fields(data)
    assert data["username"] == "Alice2"
    assert data["permissions"] == {"MEMORY": ["READ"]}

    # change username and permissions
    updated_user = {"username": "Alice3", "permissions": {"UPLOAD":["WRITE"]}}
    response = client.put(f"/users/{user_id}", headers=admin_headers, json=updated_user)
    assert response.status_code == 200
    data = response.json()
    check_user_fields(data)
    assert data["username"] == "Alice3"
    assert data["permissions"] == {"UPLOAD":["WRITE"]}

    # get list of users, should be admin, user and Alice3
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for d in data:
        check_user_fields(d)
        assert d["username"] in ["admin", "user", "Alice3"]
        if d["username"] == "Alice3":
            assert d["permissions"] == {"UPLOAD":["WRITE"]}
        elif d["username"] == "admin":
            assert d["permissions"] == get_full_permissions()
        else:
            assert d["permissions"] == get_base_permissions()

def test_delete_user(client, admin_headers):

    # delete unexisting user
    response = client.delete("/users/non_existent_id", headers=admin_headers)
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "User not found"

    # create user and obtain id
    user_id = create_new_user(client, admin_headers)["id"]

    # delete user
    response = client.delete(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id

    # check that the user is not in the db anymore
    response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "User not found"

    # check user is no more in the list of users
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2 # admin and user
    assert data[0]["username"] == "admin"
    assert data[1]["username"] == "user"


