import os
from pymemcache.client.base import Client as MemcacheClient
import json

def get_memcache_client():
	memcache_addr = os.environ.get('MEMCACHE_PORT_11211_TCP_ADDR', 'localhost')
	memcache_port = os.environ.get('MEMCACHE_PORT_11211_TCP_PORT', 11211)
	return MemcacheClient((memcache_addr, int(memcache_port)), serializer=json_serializer,
	                deserializer=json_deserializer)

def json_serializer(key, value):
    if type(value) == str:
        return value, 1
    return json.dumps(value), 2

def json_deserializer(key, value, flags):
    if flags == 1:
        return value
    if flags == 2:
        return json.loads(value)
    raise Exception("Unknown serialization format")