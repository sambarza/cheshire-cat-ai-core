from tinydb import TinyDB

from cat.utils import singleton
from cat.utils import get_data_path


@singleton
class Database:
    def __init__(self):
        self.db = TinyDB(self.get_file_name())

    def get_file_name(self):
        tinydb_file = get_data_path() + "/metadata.json"
        return tinydb_file


def get_db():
    return Database().db
