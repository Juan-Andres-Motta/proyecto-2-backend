# MediSupply Backend - Session Memory Guide

**Last Updated**: 2025-10-21
**Current Branch**: `martin/auth`
**Project Phase**: MVP Development (8 weeks / 3 sprints)

---

## Critical Context

### Project Scope
- **This Repo**: Backend microservices APIs ONLY
- **Separate Repos**: Mobile apps (iOS/Android) + Web frontend
- **Project Type**: Master's degree final project (MISW4501-4502, Universidad de Los Andes)
- **Timeline**: 8 weeks for MVP, divided into 3 sprints
- **Team**: Maximum 4 people

### What This Repo Does
✅ RESTful APIs for all business logic
✅ Database management (PostgreSQL per service)
✅ Background processing & algorithms
✅ Integration between microservices
✅ Authentication/Authorization (AWS Cognito - planned)

### What This Repo Does NOT Do
❌ UI/UX (handled by separate frontend repos)
❌ Mobile app logic beyond API consumption
❌ Web app presentation layer

---

## Business Context

### MediSupply Company Profile
- **Business**: B2B medical supply distribution
- **Geography**: Colombia, Peru, Ecuador, Mexico
- **Revenue**: $97.3M/year (targeting 10% YoY growth)
- **Distribution Centers**: 25 across 4 countries
- **Active Products**: 5,500 SKUs
- **Monthly Orders**: ~15,000
- **Institutional Clients**: ~800/month
- **Sales Force**: 150 account managers

### Critical Business Problems Being Solved
1. **$650K/year losses** from expired inventory & poor procurement coordination
2. **$400K/year losses** from cold chain failures in logistics
3. **25% order rescheduling rate** due to lack of real-time inventory visibility
4. **Only 35% of sales reps** have access to current inventory during visits

---

## Technical Architecture

### Microservices (7 Services)

| Service | Port | Purpose | DB Port |
|---------|------|---------|---------|
| **BFF** | 8000 | API Gateway for frontend apps | N/A |
| **Catalog** | 8001 | Products & Providers | 5432 |
| **Client** | 8002 | Customer Management | 5433 |
| **Delivery** | 8003 | Delivery Operations | 5434 |
| **Inventory** | 8004 | Inventory Tracking | 5435 |
| **Order** | 8005 | Order Processing | 5436 |
| **Seller** | 8006 | Seller Accounts & Plans | 5437 |

### Technology Stack
- **Language**: Python 3.13+
- **Framework**: FastAPI 0.118+
- **Database**: PostgreSQL 15 (asyncpg driver)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Package Manager**: Poetry 2.0+
- **Testing**: pytest + pytest-asyncio (70% min coverage)
- **Code Quality**: Black (88 chars), flake8, isort, SonarCloud
- **Containers**: Docker (multi-stage builds)
- **Cloud**: AWS (ECS, ECR, RDS, ALB, CloudWatch)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

### Architecture Pattern: Hexagonal (Ports & Adapters)

```
{service}/
├── src/
│   ├── domain/              # Business entities & rules
│   │   ├── entities/
│   │   ├── services/
│   │   └── exceptions.py
│   ├── application/         # Use cases (business workflows)
│   │   ├── ports/          # Abstract interfaces
│   │   ├── use_cases/
│   │   └── services/
│   ├── infrastructure/      # Framework & external tools
│   │   ├── database/
│   │   │   ├── models/     # SQLAlchemy ORM
│   │   │   └── config.py   # Session management
│   │   └── config/
│   │       └── settings.py # Pydantic settings
│   └── adapters/
│       ├── input/
│       │   ├── controllers/ # HTTP handlers (THIN)
│       │   └── schemas/     # Request/Response DTOs
│       └── output/
│           └── repositories/ # DB implementations
├── tests/
├── app.py                   # FastAPI app factory
├── main.py                  # CLI (Typer)
└── pyproject.toml
```

### Key Principles
1. **Thin Controllers**: Only delegation, no business logic
2. **Dependency Injection**: FastAPI Depends()
3. **Domain-Driven Design**: Rich entities
4. **Async-First**: All I/O async/await
5. **Global Exception Handling**: Domain exceptions → middleware

---

## MVP Requirements (Week 16 Deliverable)

### Backend APIs Required for Web Frontend

#### 1. Provider & Product Management
- ✅ Provider registration (individual)
- ✅ Product loading (individual + **bulk CSV upload**)
- ✅ Product catalog queries
- ✅ Provider management

#### 2. Seller & Sales Management
- ✅ Seller registration
- ✅ Sales plan creation & management
- ✅ Sales reports generation
- ✅ Seller performance dashboards (data endpoints)

#### 3. Inventory & Warehouse
- ✅ Product location lookup in warehouses
- ✅ Inventory queries (real-time stock levels)
- ✅ Warehouse management

#### 4. Route Optimization (CRITICAL ALGORITHM)
- ⚠️ **Delivery route generation** endpoint
  - Input: List of pending orders, available vehicles, constraints
  - Output: Optimized routes (sequence of deliveries per truck)
  - Constraint: Calculate in ≤3 seconds
  - Factors: Cold chain requirements, delivery priority, distance, product type

### Backend APIs Required for Mobile - Sales Force

#### 5. Client Management
- ✅ Client lookup/search
- ✅ Client registration
- ✅ Client details & history

#### 6. Visit Management
- ⚠️ Visit route query by date
- ⚠️ Visit registration (with geolocation)
- ⚠️ Visit history

#### 7. Order Creation
- ⚠️ Online order creation
- ✅ **Real-time inventory check** during order creation
- ⚠️ Delivery time calculation (≤2 seconds response)

#### 8. Video Processing & Recommendations (CRITICAL ALGORITHM)
- ⚠️ **Video/image upload endpoint**
  - Input: Video or photo (medical equipment, product usage)
  - Processing: Identify products, analyze usage
  - Output: Product recommendations, usage tips, compliance checks
  - Constraint: Process in ≤3 seconds
  - Use case: Sales reps capture field evidence → system recommends products

### Backend APIs Required for Mobile - Clients

#### 9. Client Self-Service
- ⚠️ Client registration (<1 second response)
- ⚠️ Order creation
- ⚠️ Order status tracking (real-time)
- ⚠️ Scheduled delivery queries

---

## Quality Attributes (Must Demonstrate)

Must implement architectural **tactics** for at least one requirement per attribute:

### 1. Security
- [ ] AWS Cognito integration (3 user groups planned)
- [ ] JWT token validation
- [ ] Role-based access control (RBAC)
- [ ] Encryption for sensitive data

### 2. Integration
- [ ] Service-to-service communication (BFF ↔ microservices)
- [ ] API versioning
- [ ] Circuit breaker pattern
- [ ] Retry mechanisms

### 3. Confidentiality
- [ ] Data encryption at rest
- [ ] Secure API communication (HTTPS)
- [ ] Audit logging for sensitive operations

### 4. Availability
- [ ] Health check endpoints (already exist)
- [ ] Graceful degradation
- [ ] Database connection pooling
- [ ] Error recovery mechanisms

### 5. Scalability
- [ ] Horizontal scaling support
- [ ] Database query optimization
- [ ] Caching strategies (Redis/in-memory)
- [ ] Async processing for heavy operations

### 6. Latency
- [ ] Response time monitoring
- [ ] Query optimization (indexes, joins)
- [ ] Caching for frequent queries
- [ ] Async/background processing

---

## Performance Requirements

### Critical Latency Targets
- **Inventory query**: ≤2 seconds
- **Product location in warehouse**: ≤1 second
- **Order status query**: ≤1 second
- **Route generation**: ≤3 seconds
- **Delivery time calculation**: ≤2 seconds
- **Video processing & recommendations**: ≤3 seconds

### Throughput
- **Base**: 100 orders/minute
- **Peak**: 400 orders/minute (1-hour bursts during health campaigns)

### Scalability (Academic Simplification)
- Support 100 concurrent users per country
- Peak: 400 total concurrent users
- **Ignore**: Multi-region, multi-AZ, geographic sharding

---

## Current Implementation Status

### ✅ Implemented & Working
- Catalog service: CRUD for products, providers, categories
- Inventory service: Warehouses, stock tracking
- Seller service: Seller accounts, sales plans
- Order service: Basic structure
- Client service: Basic structure
- Delivery service: Basic structure
- BFF: API Gateway with adapters for catalog, inventory, seller
- CI/CD: GitHub Actions with per-service change detection
- Infrastructure: AWS ECS, RDS, ALB deployment
- Docker: Multi-stage builds for all services

### ⚠️ Partially Implemented / Needs Work
- **Authentication**: NOT implemented (planned: AWS Cognito)
- **Test Coverage**: Below 70% in many services
- **Route Optimization**: NOT implemented (MVP requirement)
- **Video Processing**: NOT implemented (MVP requirement)
- **Visit Management**: Basic structure may exist, needs verification
- **Real-time Features**: Limited WebSocket/real-time support

### 🚫 Not Started (Out of Scope for This Repo)
- Mobile applications (separate repo)
- Web frontend (separate repo)
- Advanced ML recommendation engines (simplified for MVP)
- Multi-region deployment

---

## Critical Algorithms to Implement

### 1. Route Optimization Algorithm (HIGH PRIORITY)
**Status**: ⚠️ NOT IMPLEMENTED

**Purpose**: Generate optimal delivery routes for trucks

**Input**:
```python
{
  "orders": [
    {"order_id": "uuid", "client_location": {"lat": 4.6, "lon": -74.0},
     "priority": "high", "requires_cold_chain": true}
  ],
  "vehicles": [
    {"vehicle_id": "uuid", "current_location": {"lat": 4.7, "lon": -74.1},
     "cold_chain_capable": true, "capacity": 1000}
  ],
  "constraints": {
    "max_delivery_time": 24,  # hours
    "max_route_duration": 8    # hours per truck
  }
}
```

**Output**:
```python
{
  "routes": [
    {
      "vehicle_id": "uuid",
      "stops": [
        {"order_id": "uuid", "sequence": 1, "eta": "2025-10-21T10:30:00"},
        {"order_id": "uuid", "sequence": 2, "eta": "2025-10-21T11:15:00"}
      ],
      "total_distance_km": 45.3,
      "estimated_duration_minutes": 135
    }
  ]
}
```

**Constraints**:
- Response time: ≤3 seconds
- Consider: cold chain requirements, delivery priority, distance optimization
- Maintainability: ≤20 person-hours to modify algorithm

**Suggested Approach** (for MVP):
- Greedy nearest-neighbor algorithm (simple, fast)
- Group by cold chain requirements first
- Sort by priority, then optimize distance
- Future: Upgrade to genetic algorithm or OR-Tools

### 2. Video Processing & Recommendation Algorithm (HIGH PRIORITY)
**Status**: ⚠️ NOT IMPLEMENTED

**Purpose**: Process video/images from sales reps, identify products, generate recommendations

**Input**:
```python
{
  "file": "base64_encoded_video_or_image",
  "context": {
    "client_id": "uuid",
    "visit_id": "uuid",
    "location": {"lat": 4.6, "lon": -74.0}
  }
}
```

**Output**:
```python
{
  "identified_products": [
    {"product_id": "uuid", "name": "Oxígeno Concentrador", "confidence": 0.89}
  ],
  "recommendations": [
    {
      "product_id": "uuid",
      "name": "Filtro HEPA compatible",
      "reason": "Compatible with identified oxygen concentrator",
      "priority": "high"
    }
  ],
  "usage_notes": "Equipment appears to be 3+ years old, recommend maintenance kit"
}
```

**Constraints**:
- Response time: ≤3 seconds
- Image/video processing required
- Product identification + recommendation generation

**Suggested Approach** (for MVP):
- **Option 1**: AWS Rekognition Custom Labels (train on medical equipment images)
- **Option 2**: Pre-trained object detection (YOLOv8) + simple rule-based recommendations
- **Option 3**: Fake ML for demo (pattern matching on metadata + rule-based recs)
- Store results for audit trail

### 3. Real-time Inventory Check (MEDIUM PRIORITY)
**Status**: ✅ Partially implemented (basic inventory queries exist)

**Purpose**: Validate product availability across warehouses when creating orders

**Input**:
```python
{
  "products": [
    {"product_id": "uuid", "quantity": 50}
  ],
  "client_location": {"lat": 4.6, "lon": -74.0}
}
```

**Output**:
```python
{
  "available": true,
  "fulfillment_plan": [
    {
      "product_id": "uuid",
      "quantity": 50,
      "warehouse_id": "uuid",
      "warehouse_name": "Bogotá CD1",
      "estimated_delivery_hours": 6
    }
  ],
  "out_of_stock": []
}
```

**Constraints**:
- Response time: ≤2 seconds
- Consider: warehouse location, stock levels, delivery time

**Current Status**: Need to verify if warehouse distance calculation exists

---

## Authentication & Authorization (PLANNED)

**Status**: ⚠️ NOT IMPLEMENTED

**Plan**: AWS Cognito with 3 User Groups

### User Groups
1. **Admin/Management**
   - Full system access
   - Can manage providers, products, sellers, clients
   - View all reports and analytics

2. **Sales Representatives**
   - Limited to assigned clients
   - Can create orders, register visits
   - View own performance metrics
   - Upload videos/images for recommendations

3. **Institutional Clients**
   - Self-service order creation
   - View own order history & status
   - Track deliveries

### Implementation Tasks
- [ ] Configure AWS Cognito User Pool
- [ ] Create 3 user groups with permissions
- [ ] Implement JWT validation middleware in BFF
- [ ] Add role-based authorization decorators
- [ ] Protect endpoints based on user groups
- [ ] Add user context to all service calls

---

## Database Schema (Key Entities)

### Catalog Service
```sql
-- Providers
id (UUID PK), nit (UNIQUE), name, email, country, created_at, updated_at

-- Products
id (UUID PK), provider_id (FK), name, category, sku (UNIQUE),
price (DECIMAL), created_at, updated_at
```

### Inventory Service
```sql
-- Warehouses
id (UUID PK), name, location (lat/lon), country, capacity,
storage_types (general/refrigerated/frozen)

-- Inventory
id (UUID PK), product_id (FK), warehouse_id (FK), quantity,
lot_number, expiration_date, storage_temp, created_at, updated_at
```

### Seller Service
```sql
-- Sellers
id (UUID PK), name, email, country, assigned_territories (JSONB)

-- Sales Plans
id (UUID PK), seller_id (FK), target_amount (DECIMAL),
period_start, period_end, products (JSONB)
```

### Order Service
```sql
-- Orders
id (UUID PK), client_id (FK), seller_id (FK), order_date,
status (pending/confirmed/in_transit/delivered/cancelled),
delivery_date, total_amount

-- Order Items
id (UUID PK), order_id (FK), product_id (FK), quantity,
unit_price, subtotal
```

### Client Service
```sql
-- Clients (Institutional)
id (UUID PK), institution_type, tax_id (UNIQUE), name,
address, specialty, assigned_seller_id (FK), country
```

### Delivery Service
```sql
-- Deliveries
id (UUID PK), order_id (FK), vehicle_id (FK), route (JSONB),
status (pending/in_transit/delivered/failed),
temperature_log (JSONB for cold chain)

-- Vehicles
id (UUID PK), license_plate, type, cold_chain_certified (BOOL),
current_location (lat/lon), status (available/in_use/maintenance)
```

---

## Testing Strategy

### Coverage Requirements
- **Minimum**: 70% per service (CI enforced)
- **Current**: Many services below threshold ⚠️

### Test Pyramid
```
     ▲ Integration (API tests with TestClient + SQLite)
    / \
   /   \ Unit Tests (Use cases with mocked repositories)
  /     \
 /_______\ Repository Tests (SQLite in-memory)
```

### Key Fixtures (conftest.py)
```python
@pytest.fixture(scope="session")
async def test_engine():
    """SQLite in-memory for tests"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    return engine

@pytest.fixture
async def db_session(test_engine):
    """Per-test database session"""
    async_session = sessionmaker(test_engine, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest.fixture
async def async_client(db_session):
    """FastAPI test client with overridden dependencies"""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        yield client
```

### Common Commands
```bash
# Run tests with coverage
poetry run pytest --cov=src --cov-report=xml:coverage.xml -v

# Run specific test file
poetry run pytest tests/adapters/input/controllers/test_product_controller.py -v

# Run with coverage threshold
poetry run pytest --cov=src --cov-fail-under=70
```

---

## Code Quality Standards

### Formatting & Linting
```bash
# Format, lint, and check (per service)
poetry run python main.py lint
```

**Tools**:
- **Black**: 88 char line length, Python 3.13
- **flake8**: 88 char line length, excludes .venv, alembic
- **isort**: Black-compatible profile
- **SonarCloud**: Quality gates, vulnerability scanning

### Git Workflow
- **Main Branch**: `main`
- **Current Branch**: `martin/auth` (auth work in progress)
- **Strategy**: Feature branches, PR to main

---

## Development Environment

### Local Setup
```bash
# Production-like local
docker-compose up -d

# With LocalStack (AWS simulation)
docker-compose -f docker-compose.local.yml up -d

# Individual service
cd {service}
poetry install
poetry run python main.py runserver
```

### Service Access (Local)
- BFF: http://localhost:8000
- Catalog: http://localhost:8001
- Client: http://localhost:8002
- Delivery: http://localhost:8003
- Inventory: http://localhost:8004
- Order: http://localhost:8005
- Seller: http://localhost:8006

### Database Access (Local)
```bash
psql -h localhost -p 5432 -U postgres -d catalog
psql -h localhost -p 5433 -U postgres -d client
# ... etc
```

### Production (AWS)
```bash
# Health checks
curl http://medisupply-alb-2065131386.us-east-1.elb.amazonaws.com/bff/health
curl http://medisupply-alb-2065131386.us-east-1.elb.amazonaws.com/catalog/health

# Force ECS redeployment
aws ecs update-service --cluster medisupply-cluster \
  --service medisupply-bff-service --force-new-deployment
```

---

## Common Patterns

### Thin Controller
```python
@router.post("/provider")
async def create_provider(
    provider: ProviderCreate,
    use_case: CreateProviderUseCase = Depends(get_create_provider_use_case)
):
    """No business logic, just delegation"""
    created = await use_case.execute(provider.model_dump())
    return JSONResponse(content={"id": str(created.id)}, status_code=201)
```

### Exception Handling
```python
# Domain exception
class DuplicateNITException(Exception):
    pass

# Global handler in app.py
@app.exception_handler(DuplicateNITException)
async def duplicate_nit_handler(request, exc):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
```

### Dependency Injection
```python
# dependencies.py
def get_catalog_adapter(
    http_client: HttpClient = Depends(get_http_client)
) -> CatalogPort:
    return CatalogAdapter(http_client)
```

### Pydantic Settings
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str
    app_name: str = "Service"
```

---

## Pain Points & Priorities

### Known Issues
1. ⚠️ **Test Coverage** - Many services below 70%
2. ⚠️ **No Authentication** - Critical security gap
3. ⚠️ **Route Optimization** - MVP requirement not implemented
4. ⚠️ **Video Processing** - MVP requirement not implemented
5. ⚠️ **Technical Debt** - Some inconsistent patterns

### Top Priorities (Ask User)
- [ ] What to focus on in current sprint?
- [ ] Which algorithm to implement first?
- [ ] Which services need test coverage most urgently?
- [ ] Authentication timeline?

---

## Questions to Ask Before Starting Work

1. **Which sprint are we in?** (1, 2, or 3 of 8 weeks)
2. **What's the sprint goal?** (e.g., "Implement route optimization")
3. **Which services are affected?**
4. **Does this improve test coverage?**
5. **Does this address a quality attribute?**
6. **Performance requirement?** (check latency targets)
7. **Integration points?** (BFF adapter changes needed?)
8. **Database migration required?**

---

## Remember

1. **This is BACKEND ONLY** - No frontend work in this repo
2. **MVP Focus** - Not all features needed immediately (3 sprints)
3. **Academic Project** - Simplified infrastructure vs. enterprise
4. **70% Test Coverage** - Non-negotiable minimum
5. **Hexagonal Architecture** - Always follow the pattern
6. **Performance Targets** - Sub-second for critical operations
7. **Quality Attributes** - Demonstrate tactics for 6 attributes
8. **Algorithms Matter** - Route optimization & video processing are MVP requirements

---

*Last Updated: 2025-10-21*
*Current Work: Authentication implementation (martin/auth branch)*
*Next: TBD based on sprint priorities*
