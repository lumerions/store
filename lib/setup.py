from postgres import getPostgresConnection

with getPostgresConnection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                userid SERIAL PRIMARY KEY,
                sessionid TEXT NOT NULL,
                username VARCHAR(20) UNIQUE NOT NULL,
                email VARCHAR(50) NOT NULL,
                password VARCHAR(100) NOT NULL,
                emailcode VARCHAR(20),
                pendingnewemail VARCHAR(50),
                locked BOOLEAN NOT NULL,
                orderemails BOOLEAN NOT NULL,
                emailcodetime TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storeitems (
                itemid SERIAL PRIMARY KEY,
                price VARCHAR(30) NOT NULL,
                itemname VARCHAR(100) UNIQUE NOT NULL,
                imageurl TEXT NOT NULL,
                description TEXT NOT NULL,
                offsale BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            items TEXT NOT NULL,         
            total VARCHAR(30) NOT NULL,  
            delivered BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
