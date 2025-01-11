import redis
import os

from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
CACHE_EXPIRATION = 60
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
