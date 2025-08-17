import os
import pytest
from inspect import isfunction

import cat.utils as utils

from cat.mad_hatter.mad_hatter import MadHatter, Plugin
from cat.mad_hatter.decorators import CatHook, CatTool

from tests.utils import create_mock_plugin_zip, get_core_plugins_info, \
    get_core_plugins_ids, get_mock_plugin_info


# this function will be run before each test function
@pytest.fixture(scope="function")
def mad_hatter(client):  # client here injects the monkeypatched version of the cat
    # each test is given the mad_hatter instance (it's a singleton)
    yield MadHatter()


def test_instantiation_discovery(mad_hatter):

    core_plugins = get_core_plugins_info()["ids"]
    
    # Mad Hatter finds core plugins
    assert set(mad_hatter.get_core_plugins_ids()) == core_plugins # in folder
    assert set(mad_hatter.get_active_plugins()) == core_plugins   # in db
    assert set(mad_hatter.plugins.keys()) == core_plugins         # in memory

    for cp in core_plugins:
        assert isinstance(mad_hatter.plugins[cp], Plugin)
        assert isinstance(mad_hatter.plugins[cp].active, bool)
        assert mad_hatter.plugins[cp].active
        # default active plugins are stored in DB
        assert cp in mad_hatter.get_active_plugins()

    # finds hooks
    assert len(mad_hatter.hooks.keys()) == get_core_plugins_info()["unique_hooks"]
    for hook_name, hooks_list in mad_hatter.hooks.items():
        assert len(hooks_list) > 0
        h = hooks_list[0]
        assert isinstance(h, CatHook)
        assert h.plugin_id in core_plugins
        assert isinstance(h.name, str)
        assert isfunction(h.function)
        assert isinstance(h.priority, int)

    # finds tool
    assert len(mad_hatter.tools) == get_core_plugins_info()["tools"]
    tool = mad_hatter.tools[0]
    assert isinstance(tool, CatTool)
    assert tool.plugin_id in core_plugins
    assert tool.name == "get_the_time"
    assert (
        tool.description
        == "Useful to get the current time when asked. Input is always None."
    )
    assert isfunction(tool.func)
    assert not tool.return_direct
    assert len(tool.start_examples) == 2
    assert "what time is it" in tool.start_examples
    assert "get the time" in tool.start_examples


# installation tests will be run for both flat and nested plugin
@pytest.mark.parametrize("plugin_is_flat", [True, False])
def test_plugin_install(mad_hatter: MadHatter, plugin_is_flat):
    # install plugin
    new_plugin_zip_path = create_mock_plugin_zip(flat=plugin_is_flat)
    mad_hatter.install_plugin(new_plugin_zip_path)

    core_plugins = get_core_plugins_info()["ids"]

    # archive extracted
    assert os.path.exists(os.path.join(utils.get_plugins_path(), "mock_plugin"))

    # plugins list updated
    assert set(mad_hatter.plugins.keys()) == core_plugins.union({"mock_plugin"})
    assert isinstance(mad_hatter.plugins["mock_plugin"], Plugin)
    assert (
        "mock_plugin" in mad_hatter.get_active_plugins()
    )  # plugin starts active

    # plugin is activated by default
    assert isinstance(mad_hatter.plugins["mock_plugin"].active, bool)
    assert mad_hatter.plugins["mock_plugin"].active

    # plugin contains cat decorators
    assert len(mad_hatter.plugins["mock_plugin"].hooks) == get_mock_plugin_info()["hooks"]
    assert len(mad_hatter.plugins["mock_plugin"].tools) == get_mock_plugin_info()["tools"]
    assert len(mad_hatter.plugins["mock_plugin"].forms) == get_mock_plugin_info()["forms"]
    assert len(mad_hatter.plugins["mock_plugin"].endpoints) == get_mock_plugin_info()["endpoints"]

    # tool found
    new_tool = mad_hatter.plugins["mock_plugin"].tools[0]
    assert new_tool.plugin_id == "mock_plugin"
    assert id(new_tool) == id(mad_hatter.tools[1])  # cached and same object in memory!
    # tool examples found
    assert len(new_tool.start_examples) == 2
    assert "mock tool example 1" in new_tool.start_examples
    assert "mock tool example 2" in new_tool.start_examples

    # hooks found
    new_hooks = mad_hatter.plugins["mock_plugin"].hooks
    hooks_ram_addresses = []
    for h in new_hooks:
        assert h.plugin_id == "mock_plugin"
        hooks_ram_addresses.append(id(h))

    # TODOV2 fix these tests, I'm cooked
    # found tool and hook have been cached
    #mock_hook_name = "before_cat_sends_message"
    #cached_hooks = mad_hatter.hooks[mock_hook_name]
    #assert set(mad_hatter.hooks).issuperset(cached_hooks)
    
    # hook properties
    #expected_priorities = [3, 2]
    #assert len(cached_hooks) == 2  # two in mock plugin
    #for hook_idx, cached_hook in enumerate(cached_hooks):
    #    assert cached_hook.name == mock_hook_name
    #    assert (
    #        cached_hook.priority == expected_priorities[hook_idx]
    #    )  # correctly sorted by priority
    #    if cached_hook.plugin_id not in core_plugins:
    #        assert cached_hook.plugin_id == "mock_plugin"
    #        assert id(cached_hook) in hooks_ram_addresses  # same object in memory!

    # list of active plugins in DB is correct
    active_plugins = mad_hatter.get_active_plugins()
    for cp in core_plugins:
        assert cp in active_plugins
    assert "mock_plugin" in active_plugins


def test_plugin_uninstall_non_existent(mad_hatter: MadHatter):

    # default
    core_plugins = get_core_plugins_info()["ids"]
    assert set(mad_hatter.plugins.keys()) == core_plugins
    
    # should throw error
    with pytest.raises(Exception) as e:
        mad_hatter.uninstall_plugin("wrong_plugin")
        assert "PORCO DIO" in str(e)

    # still the same plugins
    assert set(mad_hatter.plugins.keys()) == core_plugins

    # list of active plugins in DB is correct
    assert set(mad_hatter.get_active_plugins()) == core_plugins


@pytest.mark.parametrize("plugin_is_flat", [True, False])
def test_plugin_uninstall(mad_hatter: MadHatter, plugin_is_flat):
    # install plugin
    new_plugin_zip_path = create_mock_plugin_zip(flat=plugin_is_flat)
    mad_hatter.install_plugin(new_plugin_zip_path)

    # uninstall
    mad_hatter.uninstall_plugin("mock_plugin")

    # directory removed
    assert not os.path.exists(os.path.join(utils.get_plugins_path(), "mock_plugin"))

    # plugins list updated
    assert "mock_plugin" not in mad_hatter.plugins.keys()
    # plugin cache updated (only core_plugins stuff)
    assert len(mad_hatter.hooks) == get_core_plugins_info()["unique_hooks"] 
    for h_name, h_list in mad_hatter.hooks.items():
        assert len(h_list) in [1, 2, 3] # TODOV2 check numerosity for each hook
        assert h_list[0].plugin_id in get_core_plugins_ids()
    assert len(mad_hatter.tools) == get_core_plugins_info()["tools"]
    assert len(mad_hatter.forms) == get_core_plugins_info()["forms"]
    assert len(mad_hatter.endpoints) == get_core_plugins_info()["endpoints"]

    # list of active plugins in DB is correct
    active_plugins = mad_hatter.get_active_plugins()
    assert set(active_plugins) == get_core_plugins_ids()


# TODOV2: should refactor the checks for core plugins as a simple function: DRY