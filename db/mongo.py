from functools import lru_cache

from pymongo import MongoClient

from config.settings import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def get_database():
    settings = get_settings()
    client = MongoClient(settings.MONGO_DB_URL, tz_aware=True)
    return client[settings.MONGO_DB_NAME]


def get_collection(collection_name: str):
    return get_database()[collection_name]
