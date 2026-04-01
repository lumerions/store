from pydantic_settings import BaseSettings

class Config(BaseSettings):
    RedisConnectionToken: str = "AfvMAAIncDFlYzAyODM4OGM0Nzg0ODBlODdkYzEyZTY3ZjExOWU3MHAxNjQ0NjA"
    RedisConnectionURL: str = "https://steady-heron-64460.upstash.io"
    PostgresConnection: str = "postgresql://neondb_owner:npg_nuc5NPZl0DJA@ep-tiny-waterfall-adb4f3n3-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require&connect_timeout=10&keepalives=1&keepalives_idle=30"
    StoreName: str = "MODERN"
    AdminUsername: str = "Admin"
    ResendAPIKey: str = "re_Pwq37GMA_BbyuATLy4p5eQhUWE9FyRwjy"
    EMAILLimit: int = 5
    EMAILWindow: int = 15 * 60
    NowPaymentsIPNSecret: str = "D/8dp2NgaLJXHk966I2NePXSMrFwCmos"
    NowPaymentsAPISecret: str = "5FW8DQ8-H814VMB-HG04DHE-0W2JTN3"
    NowPaymentsAPIURL: str = "https://api.nowpayments.io/v1/invoice"
    SUPPORTEDCOINS: dict = {
        "btc": "Bitcoin",
        "eth": "Ethereum",
        "sol": "Solana",
        "usdc": "USD Coin",
        "usdt": "Tether",
        "pyusd": "PayPal USD",
        "busd": "Binance USD",
        "ltc": "Litecoin",
        "xrp": "Ripple",
        "doge": "Dogecoin",
        "trx": "Tron",
        "bch": "Bitcoin Cash",
        "xlm": "Stellar",
        "matic": "Polygon",
        "ada": "Cardano",
        "shib": "Shiba Inu",
        "avax": "Avalanche",
        "link": "Chainlink",
        "dot": "Polkadot",
        "near": "Near Protocol",
        "atom": "Cosmos",
        "algo": "Algorand",
        "ftm": "Fantom",
        "hbar": "Hedera",
        "vet": "VeChain",
        "pepe": "Pepe",
        "uni": "Uniswap",
        "kas": "Kaspa",
        "xmr": "Monero",
        "zec": "Zcash"
    }