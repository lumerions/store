from pydantic_settings import BaseSettings

class Config(BaseSettings):
    RedisConnectionToken: str = ""
    RedisConnectionURL: str = ""
    PostgresConnection: str = ""
    StoreName: str = "MODERN"
    AdminUsername: str = "Admin"
    ResendAPIKey: str = ""
    EMAILLimit: int = 5
    EMAILWindow: int = 900
    NowPaymentsIPNSecret: str = ""
    NowPaymentsAPISecret: str = ""
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

