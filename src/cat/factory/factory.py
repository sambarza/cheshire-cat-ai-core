
from typing import Type

class Factory:

    async def instantiate_object_from_setting_name(self, cls: Type, setting_name: str):
        """Instantiate actual object from the class and its config as stored in DB"""
        pass

    async def instantiate_object_from_config(self, cls, config):
        """Instantiate actual object from the class and its config as stored in DB"""
        pass
    
    async def get_allowed_classes(self, base_csl):
        """Get classes """