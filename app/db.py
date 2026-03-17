import os
from pymongo import MongoClient

SPAR_URI = os.environ.get(
    "ADANI_MONGO_URI",
    "mongodb://tarsyer_admin:MdbTarsyerAdmin%232025%21Prod%247@database.tarsyer.com:27018/sparServer?authSource=admin"
)

_spar_client = None

def init_db(app):
    global _spar_client
    _spar_client = MongoClient(SPAR_URI, serverSelectionTimeoutMS=5000)

def get_spar_db():
    return _spar_client["sparServer"]
