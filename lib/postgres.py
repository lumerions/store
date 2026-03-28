from psycopg_pool import ConnectionPool
import psycopg
from config import Config
cfg = Config()
pool = ConnectionPool(cfg.PostgresConnection)

def getPostgresConnection():
    return pool.connection()