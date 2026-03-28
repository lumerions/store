from upstash_redis import Redis
from config import Config
cfg = Config()
redis = Redis(url=cfg.RedisConnectionURL, token=cfg.RedisConnectionToken)

def getRedisInstance():
    return redis