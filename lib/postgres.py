import psycopg
from psycopg_pool import ConnectionPool
from config import Config
cfg = Config()
pool = ConnectionPool(
    cfg.PostgresConnection,
    min_size=1,
    max_size=10,
    check=ConnectionPool.check_connection, 
    max_idle=30.0,                         
    max_lifetime=300.0,                    
    reconnect_timeout=10.0
)

def getPostgresConnection():
    return pool.connection()