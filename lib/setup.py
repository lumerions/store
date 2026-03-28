cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        userid SERIAL PRIMARY KEY,
        sessionid TEXT NOT NULL,
        username VARCHAR(20) UNIQUE NOT NULL,
        email VARCHAR(50) NOT NULL,
        password VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")