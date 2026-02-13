"""Test PostgreSQL connection."""
import asyncpg
import asyncio


async def test_connection():
    """Test database connection."""
    try:
        conn = await asyncpg.connect('postgresql://copilot_user:copilot_password@localhost/copilot_db')
        version = await conn.fetchval('SELECT version();')
        print(f"✅ Connected to PostgreSQL Database")
        print(f"   Database: copilot_db")
        print(f"   User: copilot_user")
        print(f"   Version: {version.split(',')[0]}")

        # List tables
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public';")
        if tables:
            print(f"   Tables: {len(tables)} found")
        else:
            print(f"   Tables: None (database is empty)")

        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}")
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
