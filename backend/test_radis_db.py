import os
import redis
import psycopg2
import time

def check_redis():
    """Checks the connection to Redis."""
    try:
        print("Connecting to Redis...")
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )
        r.ping()
        print("✅ Redis connection successful!")
        
        # Test SET/GET
        r.set("test_key", "hello_redis")
        value = r.get("test_key")
        print(f"✅ Redis SET/GET successful. Got value: {value}")
        
        return True
    except redis.exceptions.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def check_postgres():
    """Checks the connection to PostgreSQL."""
    try:
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "tiktok_live_db"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        print("✅ PostgreSQL connection successful!")
        
        # Test query
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print(f"✅ PostgreSQL query successful. Version: {db_version[0]}")
        
        cur.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def main():
    """Main function to run connection checks."""
    max_retries = 5
    retry_delay = 5  # seconds

    redis_ready = False
    for i in range(max_retries):
        if check_redis():
            redis_ready = True
            break
        print(f"Retrying in {retry_delay} seconds... ({i+1}/{max_retries})")
        time.sleep(retry_delay)

    postgres_ready = False
    for i in range(max_retries):
        if check_postgres():
            postgres_ready = True
            break
        print(f"Retrying in {retry_delay} seconds... ({i+1}/{max_retries})")
        time.sleep(retry_delay)

    print("\n--- Connection Check Summary ---")
    print(f"Redis: {'OK' if redis_ready else 'Failed'}")
    print(f"PostgreSQL: {'OK' if postgres_ready else 'Failed'}")
    print("--------------------------------")

if __name__ == "__main__":
    main()
