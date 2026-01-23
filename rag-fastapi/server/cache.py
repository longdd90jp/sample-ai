# cache.py
from hashlib import sha256
CACHE = {}

def cache_key(query: str, doc_ids: list[str]) -> str:
    return sha256(("||".join([query] + doc_ids)).encode()).hexdigest()

def get_cache(key: str): return CACHE.get(key)
def set_cache(key: str, val: dict): CACHE[key] = val