"""Setup PostgreSQL for OpsCopilot."""
import asyncpg
import asyncio
import sys


async def setup_database():
    """Setup PostgreSQL database and users."""

    print("📊 PostgreSQL Setup for OpsCopilot")
    print("=" * 60)

    # Step 1: Connect as admin
    print("\n[1/4] Connecting as postgres admin...")
    try:
        admin_conn = await asyncpg.connect(
            'postgresql://postgres@localhost/postgres'
        )
        print("✅ Connected as admin")
    except asyncpg.InvalidPasswordError:
        print("❌ Password required for postgres user")
        print("   Please provide postgres password in connection string")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

    try:
        # Step 2: Create user
        print("\n[2/4] Creating/updating copilot_user...")
        try:
            # Drop user if exists (cascade to drop objects)
            await admin_conn.execute(
                "DROP USER IF EXISTS copilot_user CASCADE;"
            )
            print("   • Removed existing copilot_user")
        except Exception:
            pass

        # Create new user with password
        await admin_conn.execute(
            "CREATE USER copilot_user WITH PASSWORD 'copilot_password';"
        )
        print("✅ Created copilot_user with password")

        # Step 3: Create database
        print("\n[3/4] Creating/updating copilot_db...")
        try:
            await admin_conn.execute("DROP DATABASE IF EXISTS copilot_db;")
            print("   • Removed existing copilot_db")
        except Exception:
            pass

        await admin_conn.execute(
            "CREATE DATABASE copilot_db OWNER copilot_user;"
        )
        print("✅ Created copilot_db")

        # Step 4: Grant privileges
        print("\n[4/4] Granting privileges...")
        await admin_conn.execute(
            "GRANT ALL PRIVILEGES ON DATABASE copilot_db TO copilot_user;"
        )
        await admin_conn.execute(
            "ALTER USER copilot_user CREATEDB;"
        )
        print("✅ Granted privileges to copilot_user")

        await admin_conn.close()

        # Test connection as copilot_user
        print("\n" + "=" * 60)
        print("Testing new connection as copilot_user...")
        await asyncio.sleep(1)  # Give DB time to process

        test_conn = await asyncpg.connect(
            'postgresql://copilot_user:copilot_password@localhost/copilot_db'
        )
        version = await test_conn.fetchval('SELECT version();')
        print(f"✅ Successfully connected to copilot_db")
        print(f"   User: copilot_user")
        print(f"   Database: copilot_db")
        print(f"   PostgreSQL: {version.split(',')[0]}")
        await test_conn.close()

        print("\n" + "=" * 60)
        print("✅ PostgreSQL Setup Complete!")
        print("\n🚀 You can now run:")
        print("   python run_services.py")
        print("   (Full setup with database)")
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error during setup: {type(e).__name__}")
        print(f"   {e}")
        await admin_conn.close()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(setup_database())
