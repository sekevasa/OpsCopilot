"""Initialize PostgreSQL schemas for OpsCopilot services."""
import asyncpg
import asyncio


async def create_schemas():
    """Create required schemas in the database."""

    print("📊 Creating PostgreSQL Schemas")
    print("=" * 60)

    try:
        conn = await asyncpg.connect(
            'postgresql://copilot_user:copilot_password@localhost/copilot_db'
        )

        schemas = ['staging', 'manufacturing',
                   'forecast', 'notifications', 'ai_runtime']

        for schema in schemas:
            try:
                await conn.execute(f'CREATE SCHEMA IF NOT EXISTS {schema};')
                print(f"✅ Created schema: {schema}")
            except Exception as e:
                print(f"⚠️  Schema {schema}: {e}")

        await conn.close()
        print("\n" + "=" * 60)
        print("✅ Schemas created successfully!")
        print("\n🚀 Run services again with:")
        print("   python run_services.py")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_schemas())
