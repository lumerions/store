from pydantic import BaseSettings

class Config(BaseSettings):
    PostgresConnection: str = "postgresql://neondb_owner:npg_nuc5NPZl0DJA@ep-tiny-waterfall-adb4f3n3-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"