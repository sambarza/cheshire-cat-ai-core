import os
from tortoise import Tortoise

from cat.env import get_env
from cat.log import log

DB_URL = get_env("CCAT_SQL")
if DB_URL.startswith("sqlite"):
    dialect, path = DB_URL.split(":///")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db_path = os.path.abspath(path)
    DB_URL = f"{dialect}:///{db_path}"
if DB_URL.startswith("postgresql"):
    pass

async def init_db():

    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": ["cat.db.models"]},
        
    )
    await Tortoise.generate_schemas(safe=True)

