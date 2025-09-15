import os
import glob
import shutil
import inspect
from copy import deepcopy
from typing import List, Dict, Any
from pathlib import Path

from cat.log import log
import cat.utils as utils
from cat.db.models import Setting
from cat.mad_hatter.plugin_extractor import PluginExtractor
from cat.mad_hatter.plugin import Plugin
from cat.mad_hatter.decorators.hook import CatHook
from cat.mad_hatter.decorators.tool import CatTool
from cat.mad_hatter.decorators.endpoint import CatEndpoint

from cat.experimental.form import CatForm


# This class is responsible for plugins functionality:
# - loading
# - prioritizing
# - executing
class MadHatter:
    # loads and execute plugins
    # - enter into the plugin folder and loads everything
    #   that is decorated or named properly
    # - orders plugged in hooks by name and priority
    # - exposes functionality to the cat

    def __init__(self):

        # plugins dictionary, contains all of them (active and inactive)
        # it is kept in sync with the contents of plugin folders
        # for a list of active plugins (stored in db), see MadHatter.get_active_plugins
        self.plugins: Dict[str, Plugin] = {}

        self.hooks: Dict[
            str, List[CatHook]
        ] = {}  # dict of active plugins hooks ( hook_name -> [CatHook, CatHook, ...])
        self.tools: List[CatTool] = []  # list of active plugins tools
        self.forms: List[CatForm] = []  # list of active plugins forms
        self.endpoints: List[CatEndpoint] = []  # list of active plugins endpoints


    async def install_plugin(self, package_plugin):
        # extract zip/tar file into plugin folder
        extractor = PluginExtractor(package_plugin)
        plugin_path = extractor.extract(utils.get_plugins_path())

        # remove zip after extraction
        os.remove(package_plugin)

        # get plugin id (will be its folder name)
        plugin_id = os.path.basename(plugin_path)

        # create plugin obj
        self.load_plugin(plugin_path)

        # activate it
        await self.toggle_plugin(plugin_id)

    async def uninstall_plugin(self, plugin_id):

        # plugin exists and it is not a core plugin
        if not self.plugin_exists(plugin_id):
            raise Exception(f"Plugin {plugin_id} is not installed")

        # deactivate plugin if it is active (will sync cache)
        if plugin_id in await self.get_active_plugins():
            await self.toggle_plugin(plugin_id)

        # remove plugin from cache
        plugin_path = self.plugins[plugin_id].path
        del self.plugins[plugin_id]

        # remove plugin folder
        shutil.rmtree(plugin_path)

    # discover all plugins
    async def find_plugins(self):
        # emptying plugin dictionary, plugins will be discovered from disk
        # and stored in a dictionary plugin_id -> plugin_obj
        self.plugins = {}

        # active plugins ids (stored in db)
        active_plugins = await self.get_active_plugins()

        # plugins are found in the `./plugins` folder
        # TODOV2: these two attributes are not really necessary, they can maybe be properties
        all_plugin_folders = \
            glob.glob( f"{utils.get_plugins_path()}/*/")

        log.info("Active Plugins:")
        log.info(active_plugins)

        # discover plugins, folder by folder
        for folder in all_plugin_folders:
            self.load_plugin(folder)

            plugin_id = os.path.basename(os.path.normpath(folder))

            if plugin_id in active_plugins:
                try:
                    self.plugins[plugin_id].activate()
                except Exception as e:
                    # Couldn't activate the plugin -> Deactivate it
                    if plugin_id in active_plugins:
                        await self.toggle_plugin(plugin_id)
                    raise e

        await self.sync_decorated()

    def load_plugin(self, plugin_path):
        # Instantiate plugin.
        #   If the plugin is inactive, only manifest will be loaded
        #   If active, also settings, tools and hooks
        try:
            plugin = Plugin(plugin_path)
            # if plugin is valid, keep a reference
            self.plugins[plugin.id] = plugin
        except Exception:
            # Something happened while loading the plugin.
            # Print the error and go on with the others.
            log.error(f"Error while loading plugin from {plugin_path}")

    # Load decorated functions from active plugins into MadHatter
    async def sync_decorated(self):
        # emptying tools, hooks and forms
        self.hooks = {}
        self.tools = []
        self.forms = []
        self.endpoints = []

        active_plugins = await self.get_active_plugins()

        for _, plugin in self.plugins.items():
            # load hooks, tools, forms and endpoints from active plugins
            if plugin.id in active_plugins:
                # cache tools
                self.tools += plugin.tools

                self.forms += plugin.forms

                self.endpoints += plugin.endpoints

                # cache hooks (indexed by hook name)
                for h in plugin.hooks:
                    if h.name not in self.hooks.keys():
                        self.hooks[h.name] = []
                    self.hooks[h.name].append(h)

        # sort each hooks list by priority
        for hook_name in self.hooks.keys():
            self.hooks[hook_name].sort(key=lambda x: x.priority, reverse=True)

        # notify sync has finished (the Cat will ensure all tools are embedded in vector memory)
        # TODOV2: use a hook so plugins can update tools embeddings and other post sync operations
        for endpoint in self.endpoints:
            if endpoint.plugin_id in await self.get_active_plugins():
                endpoint.activate(self.fastapi_app)

    # check if plugin exists
    def plugin_exists(self, plugin_id) -> bool:
        return plugin_id in self.plugins.keys()


    async def get_active_plugins(self):
        active_plugins = await Setting.get("active_plugins", default=[])
        return active_plugins

       
    # activate / deactivate plugin
    async def toggle_plugin(self, plugin_id):

        active_plugins = await self.get_active_plugins()

        if self.plugin_exists(plugin_id):
            plugin_is_active = plugin_id in active_plugins

            # update list of active plugins
            if plugin_is_active:
                log.warning(f"Toggle plugin {plugin_id}: Deactivate")

                # Deactivate the plugin
                self.plugins[plugin_id].deactivate()
                # Remove the plugin from the list of active plugins
                active_plugins.remove(plugin_id)
            else:
                log.warning(f"Toggle plugin {plugin_id}: Activate")

                # Activate the plugin
                try:
                    self.plugins[plugin_id].activate()
                except Exception as e:
                    # Couldn't activate the plugin
                    raise e

                # Add the plugin in the list of active plugins
                active_plugins.append(plugin_id)

            # update DB with list of active plugins, delete duplicate plugins
            await Setting.set("active_plugins", list(set(active_plugins)))

            # update cache and embeddings
            self.sync_decorated()

        else:
            raise Exception(f"Plugin {plugin_id} not present in plugins folder")

    # execute requested hook
    def execute_hook(self, hook_name, *args, cat) -> Any:
        # check if hook is supported
        if hook_name not in self.hooks.keys():
            log.debug(f"Hook {hook_name} not present in any plugin")
            if len(args)==0:
                return
            else:
                return args[0]

        # Hook has no arguments (aside cat)
        #  no need to pipe
        if len(args) == 0:
            for hook in self.hooks[hook_name]:
                try:
                    log.debug(
                        f"Executing {hook.plugin_id}::{hook.name} with priority {hook.priority}"
                    )
                    hook.function(cat=cat)
                except Exception:
                    log.error(f"Error in plugin {hook.plugin_id}::{hook.name}")
                    plugin_obj = self.plugins[hook.plugin_id]
                    log.warning(plugin_obj.plugin_specific_error_message())
            return

        # Hook with arguments.
        #  First argument is passed to `execute_hook` is the pipeable one.
        #  We call it `tea_cup` as every hook called will receive it as an input,
        #  can add sugar, milk, or whatever, and return it for the next hook
        tea_cup = deepcopy(args[0])

        # run hooks
        for hook in self.hooks[hook_name]:
            try:
                # pass tea_cup to the hooks, along other args
                # hook has at least one argument, and it will be piped
                log.debug(
                    f"Executing {hook.plugin_id}::{hook.name} with priority {hook.priority}"
                )
                tea_spoon = hook.function(
                    deepcopy(tea_cup), *deepcopy(args[1:]), cat=cat
                )
                # log.debug(f"Hook {hook.plugin_id}::{hook.name} returned {tea_spoon}")
                if tea_spoon is not None:
                    tea_cup = tea_spoon
            except Exception:
                log.error(f"Error in plugin {hook.plugin_id}::{hook.name}")
                plugin_obj = self.plugins[hook.plugin_id]
                log.warning(plugin_obj.plugin_specific_error_message())

        # tea_cup has passed through all hooks. Return final output
        return tea_cup

    # get plugin object (used from within a plugin)
    # TODO: should we allow to take directly another plugins' obj?
    # TODO: throw exception if this method is called from outside the plugins folder
    def get_plugin(self):
        # who's calling?
        calling_frame = inspect.currentframe().f_back
        # Get the module associated with the frame
        module = inspect.getmodule(calling_frame)
        # Get the absolute and then relative path of the calling module's file
        abs_path = inspect.getabsfile(module)
        
        # Replace the root and get only the current plugin folder
        plugin_suffix = os.path.normpath(
            abs_path.replace(utils.get_plugins_path() + "/", "")
        )
        # Plugin's folder
        name = plugin_suffix.split("/")[0]
        return self.plugins[name]

    @property
    def procedures(self):
        return self.tools + self.forms
