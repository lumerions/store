import psycopg
from psycopg_pool import ConnectionPool
from config import Config
cfg = Config()
pool = ConnectionPool(cfg.PostgresConnection)

def getPostgresConnection():
    return pool.connection()