from pydantic_settings import BaseSettings

class Config(BaseSettings):
    RedisConnectionToken: str = "AfvMAAIncDFlYzAyODM4OGM0Nzg0ODBlODdkYzEyZTY3ZjExOWU3MHAxNjQ0NjA"
    RedisConnectionURL: str = "https://steady-heron-64460.upstash.io"
    PostgresConnection: str = "postgresql://neondb_owner:npg_nuc5NPZl0DJA@ep-tiny-waterfall-adb4f3n3-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    StoreName: str = "MODERN"