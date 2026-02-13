# Development Guide

## Local Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- IDE (VS Code recommended)

### Initial Setup

```bash
# 1. Clone repository
git clone <repo>
cd OpsCopilot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install development dependencies
pip install -r shared/requirements.txt
pip install -r services/data-ingest-service/requirements.txt

# 4. Setup environment
cp .env.example .env

# 5. Start infrastructure
docker-compose up -d postgres redis

# 6. Run service
python services/data-ingest-service/main.py
```

## Project Structure Guidelines

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_private_method()`

### Module Organization

Each service follows:
```
service-name/
├── app/
│   ├── domain/          # Database models, schemas, repositories
│   ├── application/     # Business logic, services
│   ├── infrastructure/  # Config, logging, external clients
│   ├── api/             # HTTP routes
│   └── main.py          # FastAPI app factory
├── tests/               # Unit/integration tests
├── requirements.txt     # Service dependencies
├── Dockerfile
└── main.py              # Entry point
```

## Development Workflow

### Creating New Feature

1. **Plan in Domain Layer**
   ```python
   # app/domain/models.py
   class NewEntity(Base):
       __tablename__ = "new_entities"
       id = Column(PG_UUID, primary_key=True)
       # ... fields
   ```

2. **Add Repository**
   ```python
   # app/domain/repositories.py
   class NewEntityRepository(BaseRepository[NewEntity]):
       async def custom_query(self):
           # ...
   ```

3. **Create Schemas**
   ```python
   # app/domain/schemas.py
   class NewEntityRequest(BaseModel):
       # ... fields
   
   class NewEntityResponse(BaseModel):
       # ... fields
   ```

4. **Implement Service**
   ```python
   # app/application/services.py
   class MyService:
       async def create_entity(self, data):
           # business logic
           entity = NewEntity(...)
           return await self.repo.create(entity)
   ```

5. **Add Routes**
   ```python
   # app/api/routes.py
   @router.post("/entities")
   async def create_entity(
       request: NewEntityRequest,
       service: MyService = Depends(get_service)
   ):
       return await service.create_entity(...)
   ```

6. **Write Tests**
   ```python
   # tests/test_features.py
   @pytest.mark.asyncio
   async def test_create_entity(test_db):
       service = MyService(test_db)
       entity = await service.create_entity(data)
       assert entity.id is not None
   ```

### Code Quality

```bash
# Format code
black services/data-ingest-service/

# Sort imports
isort services/data-ingest-service/

# Type checking
mypy services/data-ingest-service/

# Linting
flake8 services/data-ingest-service/

# Run tests
pytest services/data-ingest-service/tests/ -v
```

### Testing Strategies

#### Unit Test Example
```python
@pytest.mark.asyncio
async def test_service_logic(test_db):
    """Test service in isolation."""
    service = MyService(test_db)
    
    result = await service.business_operation()
    
    assert result.id is not None
    assert result.status == "success"
```

#### Integration Test Example
```python
@pytest.fixture
async def test_db():
    """Create test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, class_=AsyncSession)
    async with session_maker() as session:
        yield session
```

#### Mocking External Services
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    """Test with mocked external service."""
    with patch("app.application.services.external_client") as mock:
        mock.get_data = AsyncMock(return_value={"key": "value"})
        # Test code
```

## Debugging

### Enable Debug Logging
```python
# In config or .env
LOG_LEVEL=DEBUG
DEBUG=true
```

### Using Debugger
```python
# VS Code .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload"
      ],
      "cwd": "${workspaceFolder}/services/data-ingest-service"
    }
  ]
}
```

### Database Inspection
```bash
# Connect to PostgreSQL
psql -U copilot_user -d copilot_db -h localhost

# List tables
\dt

# Query data
SELECT * FROM manufacturing_items LIMIT 10;
```

## Common Tasks

### Adding New Endpoint

```python
# 1. Create schema
class ItemRequest(BaseModel):
    name: str

# 2. Add repository method
async def find_by_name(self, name: str):
    stmt = select(Item).where(Item.name == name)
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()

# 3. Add service method
async def get_item_by_name(self, name: str):
    item = await self.repo.find_by_name(name)
    if not item:
        raise NotFoundError("Item", name)
    return item

# 4. Add route
@router.get("/items/{name}")
async def get_item(name: str, service: Service = Depends()):
    return await service.get_item_by_name(name)
```

### Adding Database Migration

```bash
# Generate migration
cd services/data-ingest-service
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Environment Variables

Add to `.env`:
```env
SERVICE_SPECIFIC_VAR=value
```

Access in code:
```python
from shared.config import get_settings

settings = get_settings()
value = settings.service_specific_var
```

## Performance Tips

1. **Use async/await** for all I/O operations
2. **Enable connection pooling** in database config
3. **Add indexes** to frequently queried columns
4. **Use Redis** for frequently accessed data
5. **Batch operations** when possible
6. **Monitor N+1 queries** with SQLAlchemy logging

## Documentation

- Update README.md for major changes
- Add docstrings to all functions/classes
- Keep API_REFERENCE.md in sync
- Document architecture changes in ARCHITECTURE.md

## Committing Code

```bash
# Format before commit
black .
isort .

# Run tests
pytest

# Commit with meaningful message
git commit -m "feat: add new feature description"

# Push
git push origin branch-name
```

## Release Process (Future)

1. Update version in `__init__.py`
2. Update CHANGELOG.md
3. Tag release: `git tag v1.0.0`
4. Build Docker images
5. Push to registry
6. Deploy to staging/production
