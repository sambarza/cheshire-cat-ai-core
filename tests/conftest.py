import time
import pytest
import pytest_asyncio
import os
import shutil
import importlib
from typing import Any, Generator

import warnings
from pydantic import PydanticDeprecatedSince20

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

from cat.startup import cheshire_cat_api # will instantiate the cat
from cat.looking_glass.cheshire_cat import CheshireCat
from cat.looking_glass.stray_cat import StrayCat
from cat.auth.permissions import AuthUserInfo
from cat.db.database import Database
import cat.utils
from cat.mad_hatter.plugin import Plugin
from tests.utils import create_mock_plugin_zip

from cat.mad_hatter.mad_hatter import MadHatter

from tests.utils import create_mock_plugin_zip, get_mock_plugins_path


FAKE_TIMESTAMP = 1705855981

# get rid of tmp files and folders used for testing
def clean_up_mocks():
    # clean up service files and mocks
    to_be_removed = [
        "cat/metadata-test.json",  # legacy position, now moved into mocks folder
        "tests/mocks/metadata-test.json",
        "tests/mocks/mock_plugin.zip",
        "tests/mocks/mock_plugin/settings.json",
        "tmp_test",
        "tmp_cache",
        get_mock_plugins_path(),
    ]
    for tbr in to_be_removed:
        if os.path.exists(tbr):
            if os.path.isdir(tbr):
                shutil.rmtree(tbr)
            else:
                os.remove(tbr)

    # installed with mock_plugin, here we uninstall
    os.system("uv pip uninstall -y pip-install-test")


def clean_up_envs():
    # env variables
    os.environ["CCAT_DEBUG"] = "false" # do not autoreload
    # in case tests setup a file system cache, use a different file system cache dir
    os.environ["CCAT_CACHE_DIR"] = "tmp_test"


def monkey_patches(mp):

    # monkeypatch classes
    # (substitute classes' methods where necessary for testing purposes)

    # Use mock utils plugin folder
    mp.setattr(
        cat.utils,
        'get_plugins_path',
        get_mock_plugins_path
    )
    
    # Use a different json settings db
    def mock_get_file_name(self, *args, **kwargs):
        return "tests/mocks/metadata-test.json"
    mp.setattr(Database().__class__, "get_file_name", mock_get_file_name)

    # TODOV2: maybe with uv this is fast enough
    # do not check plugin dependencies at every restart
    #def mock_install_requirements(self, *args, **kwargs):
    #    pass
    #from cat.mad_hatter.plugin import Plugin
    #mp.setattr(Plugin, "_install_requirements", mock_install_requirements)

    # delete all singletons!!!
    mp.setattr(
        cat.utils.singleton,
        "instances",
        {}
    )

####################################
# Main fixture for the FastAPI app #
####################################
@pytest.fixture(scope="function")
def client(monkeypatch) -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient.
    """
    
    clean_up_mocks()
    clean_up_envs()

    # change methods for testing purposes
    monkey_patches(monkeypatch)
    
    with TestClient(cheshire_cat_api) as client:
        yield client

    # clean up tmp files and folders (useful when tests fail)
    clean_up_mocks()

######################################
# Async version of the main fixturep #
######################################
@pytest_asyncio.fixture(scope="function")
async def async_client(monkeypatch):
    clean_up_mocks()
    clean_up_envs()
    monkey_patches(monkeypatch)
    async with LifespanManager(cheshire_cat_api):
        async with AsyncClient(
            transport=ASGITransport(app=cheshire_cat_api), base_url="http://test"
        ) as ac:
            yield ac
    clean_up_mocks()

# This fixture sets the CCAT_API_KEY and CCAT_API_KEY_WS environment variables,
# making mandatory for clients to possess api keys or JWT
@pytest.fixture(scope="function")
def secure_client(client):
    # set ENV variables
    os.environ["CCAT_API_KEY"] = "meow_http"
    os.environ["CCAT_API_KEY_WS"] = "meow_ws"
    os.environ["CCAT_JWT_SECRET"] = "meow_jwt"
    yield client
    del os.environ["CCAT_API_KEY"]
    del os.environ["CCAT_API_KEY_WS"]
    del os.environ["CCAT_JWT_SECRET"]


# This fixture is useful to write tests in which
#   a plugin was just uploaded via http.
#   It wraps any test function having `just_installed_plugin` as an argument
@pytest.fixture(scope="function")
def just_installed_plugin(client):
    ### executed before each test function

    # create zip file with a plugin
    zip_path = create_mock_plugin_zip(flat=True)
    zip_file_name = zip_path.split("/")[-1]  # mock_plugin.zip in tests/mocks folder

    # upload plugin via endpoint
    with open(zip_path, "rb") as f:
        response = client.post(
            "/plugins/upload/", files={"file": (zip_file_name, f, "application/zip")}
        )

    # request was processed
    assert response.status_code == 200
    assert response.json()["filename"] == zip_file_name

    ### each test function having `just_installed_plugin` as argument, is run here
    yield
    ###

    # clean up of zip file and mock_plugin_folder is done for every test automatically (see client fixture)

# fixtures to test the main agent
@pytest.fixture(scope="function")
def main_agent(async_client):
    yield cheshire_cat_api.state.ccat.main_agent  # each test receives as argument the main agent instance

# fixture to have available an instance of StrayCat
@pytest.fixture(scope="function")
def stray(async_client):
    user_data = AuthUserInfo(
        id="Alice",
        name="Alice"
    )
    stray_cat = StrayCat(user_data)
    stray_cat.working_memory.user_message_json = {"user_id": user_data.id, "text": "meow"}
    yield stray_cat

# autouse fixture will be applied to *all* the tests
@pytest.fixture(autouse=True, scope="function")
def apply_warning_filters():
    # ignore deprecation warnings due to langchain not updating to pydantic v2
    warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)

#fixture for mock time.time function
@pytest.fixture(scope="function")
def patch_time_now(monkeypatch):

    def mytime():
        return FAKE_TIMESTAMP

    monkeypatch.setattr(time, 'time', mytime)

#fixture for mad hatter with mock plugin installed
@pytest.fixture(scope="function")
def mad_hatter_with_mock_plugin(client):  # client here injects the monkeypatched version of the cat

    # each test is given the mad_hatter instance (it's a singleton)
    mad_hatter = MadHatter()

    # install plugin
    new_plugin_zip_path = create_mock_plugin_zip(flat=True)
    mad_hatter.install_plugin(new_plugin_zip_path)

    yield mad_hatter

    # remove plugin (unless the test already removed it)
    if mad_hatter.plugin_exists("mock_plugin"):
        mad_hatter.uninstall_plugin("mock_plugin")
