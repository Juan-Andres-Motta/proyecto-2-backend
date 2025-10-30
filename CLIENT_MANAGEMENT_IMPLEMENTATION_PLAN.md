# Client Management Implementation Plan

## Overview
Implementation of client (institutional customer) management functionality from BFF to Client microservice, including authentication integration with AWS Cognito.

---

## 1. Database Schema Updates

### Client Entity (Client Microservice)

```python
# client/src/domain/entities/client.py

@dataclass
class Client:
    """Client entity representing institutional customers."""

    cliente_id: str  # UUID
    cognito_user_id: str  # Link to Cognito sub claim
    email: str  # For authentication and contact
    telefono: str  # Phone number
    nombre_institucion: str  # Institution name
    tipo_institucion: str  # Enum: hospital, clinica, laboratorio, centro_diagnostico
    nit: str  # Tax ID number
    direccion: str  # Physical address
    ciudad: str  # City
    pais: str  # Country
    representante: str  # Representative/main contact name
    vendedor_asignado_id: Optional[str] = None  # FK to seller (optional)
    creado_en: datetime = field(default_factory=datetime.utcnow)
    actualizado_en: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate client data."""
        if self.tipo_institucion not in ['hospital', 'clinica', 'laboratorio', 'centro_diagnostico']:
            raise ValueError(f"Invalid tipo_institucion: {self.tipo_institucion}")
```

### Database Migration (Alembic)

```python
# client/migrations/versions/xxx_add_client_contact_fields.py

def upgrade():
    # Add new columns
    op.add_column('clientes', sa.Column('email', sa.String(255), nullable=False))
    op.add_column('clientes', sa.Column('telefono', sa.String(50), nullable=False))
    op.add_column('clientes', sa.Column('cognito_user_id', sa.String(255), nullable=False))

    # Add unique constraint on email
    op.create_unique_constraint('uq_clientes_email', 'clientes', ['email'])

    # Add unique constraint on cognito_user_id
    op.create_unique_constraint('uq_clientes_cognito_user_id', 'clientes', ['cognito_user_id'])

    # Add index on vendedor_asignado_id for faster lookups
    op.create_index('ix_clientes_vendedor_asignado_id', 'clientes', ['vendedor_asignado_id'])

def downgrade():
    op.drop_index('ix_clientes_vendedor_asignado_id', 'clientes')
    op.drop_constraint('uq_clientes_cognito_user_id', 'clientes')
    op.drop_constraint('uq_clientes_email', 'clientes')
    op.drop_column('clientes', 'cognito_user_id')
    op.drop_column('clientes', 'telefono')
    op.drop_column('clientes', 'email')
```

---

## 2. Client Microservice Implementation

### 2.1 Domain Layer

#### Value Objects
```python
# client/src/domain/value_objects.py

class TipoInstitucion(str, Enum):
    """Enumeration for institution types."""
    HOSPITAL = "hospital"
    CLINICA = "clinica"
    LABORATORIO = "laboratorio"
    CENTRO_DIAGNOSTICO = "centro_diagnostico"

@dataclass(frozen=True)
class Email:
    """Email value object with validation."""
    value: str

    def __post_init__(self):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.value):
            raise ValueError(f"Invalid email format: {self.value}")

@dataclass(frozen=True)
class Telefono:
    """Phone number value object with validation."""
    value: str

    def __post_init__(self):
        # Basic validation - can be enhanced
        if not re.match(r'^\+?[\d\s\-()]+$', self.value):
            raise ValueError(f"Invalid phone format: {self.value}")
```

#### Repository Interface
```python
# client/src/domain/repositories/client_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.client import Client

class ClientRepository(ABC):
    """Repository interface for Client entity."""

    @abstractmethod
    async def create(self, client: Client) -> Client:
        """Create a new client."""
        pass

    @abstractmethod
    async def get_by_id(self, cliente_id: str) -> Optional[Client]:
        """Get client by ID."""
        pass

    @abstractmethod
    async def get_by_cognito_user_id(self, cognito_user_id: str) -> Optional[Client]:
        """Get client by Cognito user ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Client]:
        """Get client by email."""
        pass

    @abstractmethod
    async def update(self, client: Client) -> Client:
        """Update existing client."""
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Client]:
        """List all clients with pagination."""
        pass

    @abstractmethod
    async def list_by_seller(self, vendedor_asignado_id: str, skip: int = 0, limit: int = 100) -> List[Client]:
        """List clients assigned to a specific seller."""
        pass

    @abstractmethod
    async def delete(self, cliente_id: str) -> bool:
        """Delete a client."""
        pass
```

### 2.2 Application Layer

#### Use Cases
```python
# client/src/application/use_cases/create_client.py

from dataclasses import dataclass
from typing import Optional
from ...domain.entities.client import Client
from ...domain.repositories.client_repository import ClientRepository
from ...domain.value_objects import Email, Telefono, TipoInstitucion

@dataclass
class CreateClientCommand:
    """Command for creating a new client."""
    cognito_user_id: str
    email: str
    telefono: str
    nombre_institucion: str
    tipo_institucion: str
    nit: str
    direccion: str
    ciudad: str
    pais: str
    representante: str
    vendedor_asignado_id: Optional[str] = None

class CreateClientUseCase:
    """Use case for creating a new client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, command: CreateClientCommand) -> Client:
        """Execute the create client use case."""

        # Validate email doesn't already exist
        existing_client = await self.client_repository.get_by_email(command.email)
        if existing_client:
            raise ValueError(f"Client with email {command.email} already exists")

        # Validate cognito_user_id doesn't already exist
        existing_cognito = await self.client_repository.get_by_cognito_user_id(command.cognito_user_id)
        if existing_cognito:
            raise ValueError(f"Client with cognito_user_id {command.cognito_user_id} already exists")

        # Validate value objects
        email = Email(command.email)
        telefono = Telefono(command.telefono)
        tipo = TipoInstitucion(command.tipo_institucion)

        # Create client entity
        client = Client(
            cliente_id=str(uuid.uuid4()),
            cognito_user_id=command.cognito_user_id,
            email=email.value,
            telefono=telefono.value,
            nombre_institucion=command.nombre_institucion,
            tipo_institucion=tipo.value,
            nit=command.nit,
            direccion=command.direccion,
            ciudad=command.ciudad,
            pais=command.pais,
            representante=command.representante,
            vendedor_asignado_id=command.vendedor_asignado_id
        )

        # Persist
        return await self.client_repository.create(client)


# client/src/application/use_cases/update_client.py

@dataclass
class UpdateClientCommand:
    """Command for updating a client."""
    cliente_id: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    nombre_institucion: Optional[str] = None
    tipo_institucion: Optional[str] = None
    nit: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    pais: Optional[str] = None
    representante: Optional[str] = None
    vendedor_asignado_id: Optional[str] = None

class UpdateClientUseCase:
    """Use case for updating a client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, command: UpdateClientCommand) -> Client:
        """Execute the update client use case."""

        # Get existing client
        client = await self.client_repository.get_by_id(command.cliente_id)
        if not client:
            raise ValueError(f"Client {command.cliente_id} not found")

        # Update fields if provided
        if command.email:
            # Check if email already used by another client
            existing = await self.client_repository.get_by_email(command.email)
            if existing and existing.cliente_id != command.cliente_id:
                raise ValueError(f"Email {command.email} already in use")
            Email(command.email)  # Validate
            client.email = command.email

        if command.telefono:
            Telefono(command.telefono)  # Validate
            client.telefono = command.telefono

        if command.nombre_institucion:
            client.nombre_institucion = command.nombre_institucion

        if command.tipo_institucion:
            TipoInstitucion(command.tipo_institucion)  # Validate
            client.tipo_institucion = command.tipo_institucion

        if command.nit:
            client.nit = command.nit

        if command.direccion:
            client.direccion = command.direccion

        if command.ciudad:
            client.ciudad = command.ciudad

        if command.pais:
            client.pais = command.pais

        if command.representante:
            client.representante = command.representante

        if command.vendedor_asignado_id is not None:  # Allow setting to None
            client.vendedor_asignado_id = command.vendedor_asignado_id

        client.actualizado_en = datetime.utcnow()

        # Persist
        return await self.client_repository.update(client)


# client/src/application/use_cases/assign_seller.py

@dataclass
class AssignSellerCommand:
    """Command for assigning a seller to a client."""
    cliente_id: str
    vendedor_asignado_id: Optional[str]  # None to unassign

class AssignSellerToClientUseCase:
    """Use case for assigning/unassigning a seller to a client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, command: AssignSellerCommand) -> Client:
        """Execute the assign seller use case."""

        client = await self.client_repository.get_by_id(command.cliente_id)
        if not client:
            raise ValueError(f"Client {command.cliente_id} not found")

        client.vendedor_asignado_id = command.vendedor_asignado_id
        client.actualizado_en = datetime.utcnow()

        return await self.client_repository.update(client)
```

### 2.3 Infrastructure Layer

#### SQLAlchemy Models
```python
# client/src/infrastructure/models/client_model.py

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.sql import func
from .base import Base

class ClientModel(Base):
    """SQLAlchemy model for Client entity."""

    __tablename__ = 'clientes'

    cliente_id = Column(String(36), primary_key=True)
    cognito_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    telefono = Column(String(50), nullable=False)
    nombre_institucion = Column(String(255), nullable=False)
    tipo_institucion = Column(String(50), nullable=False)
    nit = Column(String(50), nullable=False, index=True)
    direccion = Column(String(500), nullable=False)
    ciudad = Column(String(100), nullable=False)
    pais = Column(String(100), nullable=False)
    representante = Column(String(255), nullable=False)
    vendedor_asignado_id = Column(String(36), nullable=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_clientes_ciudad_pais', 'ciudad', 'pais'),
        Index('ix_clientes_tipo_institucion', 'tipo_institucion'),
    )
```

#### Repository Implementation
```python
# client/src/infrastructure/repositories/sqlalchemy_client_repository.py

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...domain.entities.client import Client
from ...domain.repositories.client_repository import ClientRepository
from ..models.client_model import ClientModel

class SQLAlchemyClientRepository(ClientRepository):
    """SQLAlchemy implementation of ClientRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: ClientModel) -> Client:
        """Convert SQLAlchemy model to domain entity."""
        return Client(
            cliente_id=model.cliente_id,
            cognito_user_id=model.cognito_user_id,
            email=model.email,
            telefono=model.telefono,
            nombre_institucion=model.nombre_institucion,
            tipo_institucion=model.tipo_institucion,
            nit=model.nit,
            direccion=model.direccion,
            ciudad=model.ciudad,
            pais=model.pais,
            representante=model.representante,
            vendedor_asignado_id=model.vendedor_asignado_id,
            creado_en=model.creado_en,
            actualizado_en=model.actualizado_en
        )

    def _to_model(self, entity: Client) -> ClientModel:
        """Convert domain entity to SQLAlchemy model."""
        return ClientModel(
            cliente_id=entity.cliente_id,
            cognito_user_id=entity.cognito_user_id,
            email=entity.email,
            telefono=entity.telefono,
            nombre_institucion=entity.nombre_institucion,
            tipo_institucion=entity.tipo_institucion,
            nit=entity.nit,
            direccion=entity.direccion,
            ciudad=entity.ciudad,
            pais=entity.pais,
            representante=entity.representante,
            vendedor_asignado_id=entity.vendedor_asignado_id,
            creado_en=entity.creado_en,
            actualizado_en=entity.actualizado_en
        )

    async def create(self, client: Client) -> Client:
        """Create a new client."""
        model = self._to_model(client)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, cliente_id: str) -> Optional[Client]:
        """Get client by ID."""
        result = await self.session.execute(
            select(ClientModel).where(ClientModel.cliente_id == cliente_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_cognito_user_id(self, cognito_user_id: str) -> Optional[Client]:
        """Get client by Cognito user ID."""
        result = await self.session.execute(
            select(ClientModel).where(ClientModel.cognito_user_id == cognito_user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[Client]:
        """Get client by email."""
        result = await self.session.execute(
            select(ClientModel).where(ClientModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, client: Client) -> Client:
        """Update existing client."""
        result = await self.session.execute(
            select(ClientModel).where(ClientModel.cliente_id == client.cliente_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Client {client.cliente_id} not found")

        # Update fields
        model.email = client.email
        model.telefono = client.telefono
        model.nombre_institucion = client.nombre_institucion
        model.tipo_institucion = client.tipo_institucion
        model.nit = client.nit
        model.direccion = client.direccion
        model.ciudad = client.ciudad
        model.pais = client.pais
        model.representante = client.representante
        model.vendedor_asignado_id = client.vendedor_asignado_id
        model.actualizado_en = client.actualizado_en

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Client]:
        """List all clients with pagination."""
        result = await self.session.execute(
            select(ClientModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def list_by_seller(self, vendedor_asignado_id: str, skip: int = 0, limit: int = 100) -> List[Client]:
        """List clients assigned to a specific seller."""
        result = await self.session.execute(
            select(ClientModel)
            .where(ClientModel.vendedor_asignado_id == vendedor_asignado_id)
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def delete(self, cliente_id: str) -> bool:
        """Delete a client."""
        result = await self.session.execute(
            select(ClientModel).where(ClientModel.cliente_id == cliente_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False

        await self.session.delete(model)
        await self.session.commit()
        return True
```

### 2.4 API Layer (FastAPI)

#### Schemas
```python
# client/src/infrastructure/api/schemas.py

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class TipoInstitucionEnum(str, Enum):
    """Enumeration for institution types."""
    hospital = "hospital"
    clinica = "clinica"
    laboratorio = "laboratorio"
    centro_diagnostico = "centro_diagnostico"

class ClientCreateRequest(BaseModel):
    """Request schema for creating a client."""
    email: EmailStr
    telefono: str = Field(..., min_length=7, max_length=50)
    nombre_institucion: str = Field(..., min_length=2, max_length=255)
    tipo_institucion: TipoInstitucionEnum
    nit: str = Field(..., min_length=5, max_length=50)
    direccion: str = Field(..., min_length=10, max_length=500)
    ciudad: str = Field(..., min_length=2, max_length=100)
    pais: str = Field(..., min_length=2, max_length=100)
    representante: str = Field(..., min_length=3, max_length=255)
    vendedor_asignado_id: Optional[str] = Field(None, max_length=36)

    @validator('telefono')
    def validate_telefono(cls, v):
        """Validate phone number format."""
        if not re.match(r'^\+?[\d\s\-()]+$', v):
            raise ValueError('Invalid phone number format')
        return v

class ClientUpdateRequest(BaseModel):
    """Request schema for updating a client."""
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=7, max_length=50)
    nombre_institucion: Optional[str] = Field(None, min_length=2, max_length=255)
    tipo_institucion: Optional[TipoInstitucionEnum] = None
    nit: Optional[str] = Field(None, min_length=5, max_length=50)
    direccion: Optional[str] = Field(None, min_length=10, max_length=500)
    ciudad: Optional[str] = Field(None, min_length=2, max_length=100)
    pais: Optional[str] = Field(None, min_length=2, max_length=100)
    representante: Optional[str] = Field(None, min_length=3, max_length=255)
    vendedor_asignado_id: Optional[str] = Field(None, max_length=36)

class AssignSellerRequest(BaseModel):
    """Request schema for assigning a seller to a client."""
    vendedor_asignado_id: Optional[str] = Field(None, max_length=36)

class ClientResponse(BaseModel):
    """Response schema for client."""
    cliente_id: str
    cognito_user_id: str
    email: str
    telefono: str
    nombre_institucion: str
    tipo_institucion: str
    nit: str
    direccion: str
    ciudad: str
    pais: str
    representante: str
    vendedor_asignado_id: Optional[str]
    creado_en: datetime
    actualizado_en: datetime

    class Config:
        from_attributes = True

class ClientListResponse(BaseModel):
    """Response schema for list of clients."""
    clients: list[ClientResponse]
    total: int
    skip: int
    limit: int
```

#### Controller
```python
# client/src/infrastructure/api/controllers/client_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import (
    ClientCreateRequest,
    ClientUpdateRequest,
    AssignSellerRequest,
    ClientResponse,
    ClientListResponse
)
from ....application.use_cases.create_client import CreateClientUseCase, CreateClientCommand
from ....application.use_cases.update_client import UpdateClientUseCase, UpdateClientCommand
from ....application.use_cases.assign_seller import AssignSellerToClientUseCase, AssignSellerCommand
from ...repositories.sqlalchemy_client_repository import SQLAlchemyClientRepository
from ..dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
    description="Create a new institutional client. Only authenticated client users can create their profile.",
    responses={
        201: {"description": "Client created successfully"},
        400: {"description": "Invalid request data"},
        409: {"description": "Client already exists"},
        401: {"description": "Unauthorized - Invalid or missing token"},
    }
)
async def create_client(
    request: ClientCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Create a new client profile."""

    # Ensure user is a client user
    user_groups = current_user.get("cognito:groups", [])
    if "client_users" not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only client users can create client profiles"
        )

    # Get cognito_user_id from token
    cognito_user_id = current_user.get("sub")
    if not cognito_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token: missing user ID"
        )

    try:
        # Create use case
        repository = SQLAlchemyClientRepository(session)
        use_case = CreateClientUseCase(repository)

        # Execute
        command = CreateClientCommand(
            cognito_user_id=cognito_user_id,
            email=request.email,
            telefono=request.telefono,
            nombre_institucion=request.nombre_institucion,
            tipo_institucion=request.tipo_institucion.value,
            nit=request.nit,
            direccion=request.direccion,
            ciudad=request.ciudad,
            pais=request.pais,
            representante=request.representante,
            vendedor_asignado_id=request.vendedor_asignado_id
        )

        client = await use_case.execute(command)

        return ClientResponse.from_orm(client)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating client: {str(e)}"
        )


@router.get(
    "/me",
    response_model=ClientResponse,
    summary="Get current client profile",
    description="Get the profile of the authenticated client user.",
    responses={
        200: {"description": "Client profile retrieved successfully"},
        404: {"description": "Client profile not found"},
        401: {"description": "Unauthorized - Invalid or missing token"},
    }
)
async def get_my_client_profile(
    session: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Get current authenticated client's profile."""

    cognito_user_id = current_user.get("sub")

    repository = SQLAlchemyClientRepository(session)
    client = await repository.get_by_cognito_user_id(cognito_user_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found"
        )

    return ClientResponse.from_orm(client)


@router.get(
    "/{cliente_id}",
    response_model=ClientResponse,
    summary="Get client by ID",
    description="Get a specific client by their ID. Web users only.",
    responses={
        200: {"description": "Client retrieved successfully"},
        404: {"description": "Client not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Web users only"},
    }
)
async def get_client(
    cliente_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Get a client by ID."""

    # Only web users can view other clients
    user_groups = current_user.get("cognito:groups", [])
    if "web_users" not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only web users can view client details"
        )

    repository = SQLAlchemyClientRepository(session)
    client = await repository.get_by_id(cliente_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {cliente_id} not found"
        )

    return ClientResponse.from_orm(client)


@router.get(
    "",
    response_model=ClientListResponse,
    summary="List all clients",
    description="List all clients with pagination. Web users only.",
    responses={
        200: {"description": "Clients retrieved successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Web users only"},
    }
)
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """List all clients with pagination."""

    # Only web users can list clients
    user_groups = current_user.get("cognito:groups", [])
    if "web_users" not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only web users can list clients"
        )

    repository = SQLAlchemyClientRepository(session)
    clients = await repository.list_all(skip=skip, limit=limit)

    return ClientListResponse(
        clients=[ClientResponse.from_orm(c) for c in clients],
        total=len(clients),  # TODO: Add count query
        skip=skip,
        limit=limit
    )


@router.put(
    "/{cliente_id}",
    response_model=ClientResponse,
    summary="Update client",
    description="Update a client. Client users can only update their own profile. Web users can update any client.",
    responses={
        200: {"description": "Client updated successfully"},
        404: {"description": "Client not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Cannot update other clients"},
    }
)
async def update_client(
    cliente_id: str,
    request: ClientUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Update a client."""

    user_groups = current_user.get("cognito:groups", [])
    cognito_user_id = current_user.get("sub")

    # Check authorization
    if "web_users" not in user_groups:
        # Client users can only update their own profile
        repository = SQLAlchemyClientRepository(session)
        client = await repository.get_by_id(cliente_id)

        if not client or client.cognito_user_id != cognito_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )

    try:
        repository = SQLAlchemyClientRepository(session)
        use_case = UpdateClientUseCase(repository)

        command = UpdateClientCommand(
            cliente_id=cliente_id,
            email=request.email,
            telefono=request.telefono,
            nombre_institucion=request.nombre_institucion,
            tipo_institucion=request.tipo_institucion.value if request.tipo_institucion else None,
            nit=request.nit,
            direccion=request.direccion,
            ciudad=request.ciudad,
            pais=request.pais,
            representante=request.representante,
            vendedor_asignado_id=request.vendedor_asignado_id
        )

        client = await use_case.execute(command)

        return ClientResponse.from_orm(client)

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating client: {str(e)}"
        )


@router.patch(
    "/{cliente_id}/assign-seller",
    response_model=ClientResponse,
    summary="Assign seller to client",
    description="Assign or unassign a seller to a client. Web users (administrators) only.",
    responses={
        200: {"description": "Seller assigned successfully"},
        404: {"description": "Client not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Web users only"},
    }
)
async def assign_seller_to_client(
    cliente_id: str,
    request: AssignSellerRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Assign or unassign a seller to a client."""

    # Only web users (administrators) can assign sellers
    user_groups = current_user.get("cognito:groups", [])
    if "web_users" not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign sellers to clients"
        )

    try:
        repository = SQLAlchemyClientRepository(session)
        use_case = AssignSellerToClientUseCase(repository)

        command = AssignSellerCommand(
            cliente_id=cliente_id,
            vendedor_asignado_id=request.vendedor_asignado_id
        )

        client = await use_case.execute(command)

        return ClientResponse.from_orm(client)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning seller: {str(e)}"
        )
```

---

## 3. BFF Layer Implementation

### 3.1 BFF Schemas
```python
# bff/common/clients/schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TipoInstitucionEnum(str, Enum):
    """Enumeration for institution types."""
    hospital = "hospital"
    clinica = "clinica"
    laboratorio = "laboratorio"
    centro_diagnostico = "centro_diagnostico"

class ClientCreateRequest(BaseModel):
    """BFF request schema for creating a client."""
    email: EmailStr
    telefono: str = Field(..., min_length=7, max_length=50, description="Phone number with country code")
    nombre_institucion: str = Field(..., min_length=2, max_length=255, description="Institution name")
    tipo_institucion: TipoInstitucionEnum = Field(..., description="Type of institution")
    nit: str = Field(..., min_length=5, max_length=50, description="Tax identification number")
    direccion: str = Field(..., min_length=10, max_length=500, description="Physical address")
    ciudad: str = Field(..., min_length=2, max_length=100, description="City")
    pais: str = Field(..., min_length=2, max_length=100, description="Country")
    representante: str = Field(..., min_length=3, max_length=255, description="Representative name")
    vendedor_asignado_id: Optional[str] = Field(None, max_length=36, description="Assigned seller ID (optional)")

class ClientUpdateRequest(BaseModel):
    """BFF request schema for updating a client."""
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=7, max_length=50)
    nombre_institucion: Optional[str] = Field(None, min_length=2, max_length=255)
    tipo_institucion: Optional[TipoInstitucionEnum] = None
    nit: Optional[str] = Field(None, min_length=5, max_length=50)
    direccion: Optional[str] = Field(None, min_length=10, max_length=500)
    ciudad: Optional[str] = Field(None, min_length=2, max_length=100)
    pais: Optional[str] = Field(None, min_length=2, max_length=100)
    representante: Optional[str] = Field(None, min_length=3, max_length=255)

class AssignSellerRequest(BaseModel):
    """BFF request schema for assigning a seller."""
    vendedor_asignado_id: Optional[str] = Field(None, max_length=36)

class ClientResponse(BaseModel):
    """BFF response schema for client."""
    cliente_id: str
    email: str
    telefono: str
    nombre_institucion: str
    tipo_institucion: str
    nit: str
    direccion: str
    ciudad: str
    pais: str
    representante: str
    vendedor_asignado_id: Optional[str]
    creado_en: datetime
    actualizado_en: datetime

class ClientListResponse(BaseModel):
    """BFF response schema for list of clients."""
    clients: list[ClientResponse]
    total: int
    skip: int
    limit: int
```

### 3.2 BFF Service
```python
# bff/common/clients/client_service.py

import httpx
from typing import Optional, List
from fastapi import HTTPException, status
import logging

from config import settings
from .schemas import (
    ClientCreateRequest,
    ClientUpdateRequest,
    AssignSellerRequest,
    ClientResponse,
    ClientListResponse
)

logger = logging.getLogger(__name__)


class ClientService:
    """Service for interacting with Client microservice."""

    def __init__(self, client_service_url: str):
        self.client_service_url = client_service_url

    async def create_client(
        self,
        request: ClientCreateRequest,
        access_token: str
    ) -> ClientResponse:
        """Create a new client."""

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.client_service_url}/clients",
                    json=request.dict(),
                    headers=headers
                )

                if response.status_code == 201:
                    return ClientResponse(**response.json())
                elif response.status_code == 409:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=response.json().get("detail", "Client already exists")
                    )
                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials"
                    )
                elif response.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=response.json().get("detail", "Forbidden")
                    )
                else:
                    logger.error(f"Client service error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error creating client"
                    )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling client service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Client service temporarily unavailable"
            )

    async def get_my_profile(self, access_token: str) -> ClientResponse:
        """Get current client's profile."""

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.client_service_url}/clients/me",
                    headers=headers
                )

                if response.status_code == 200:
                    return ClientResponse(**response.json())
                elif response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Client profile not found"
                    )
                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials"
                    )
                else:
                    logger.error(f"Client service error: {response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error retrieving client profile"
                    )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling client service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Client service temporarily unavailable"
            )

    async def get_client(self, cliente_id: str, access_token: str) -> ClientResponse:
        """Get a client by ID."""

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.client_service_url}/clients/{cliente_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    return ClientResponse(**response.json())
                elif response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Client {cliente_id} not found"
                    )
                elif response.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only web users can view client details"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error retrieving client"
                    )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling client service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Client service temporarily unavailable"
            )

    async def list_clients(
        self,
        skip: int,
        limit: int,
        access_token: str
    ) -> ClientListResponse:
        """List all clients with pagination."""

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.client_service_url}/clients",
                    params={"skip": skip, "limit": limit},
                    headers=headers
                )

                if response.status_code == 200:
                    return ClientListResponse(**response.json())
                elif response.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only web users can list clients"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error listing clients"
                    )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling client service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Client service temporarily unavailable"
            )

    async def update_client(
        self,
        cliente_id: str,
        request: ClientUpdateRequest,
        access_token: str
    ) -> ClientResponse:
        """Update a client."""

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.client_service_url}/clients/{cliente_id}",
                    json=request.dict(exclude_unset=True),
                    headers=headers
                )

                if response.status_code == 200:
                    return ClientResponse(**response.json())
                elif response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Client {cliente_id} not found"
                    )
                elif response.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only update your own profile"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error updating client"
                    )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling client service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Client service temporarily unavailable"
            )

    async def assign_seller(
        self,
        cliente_id: str,
        request: AssignSellerRequest,
        access_token: str
    ) -> ClientResponse:
        """Assign a seller to a client."""

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.client_service_url}/clients/{cliente_id}/assign-seller",
                    json=request.dict(),
                    headers=headers
                )

                if response.status_code == 200:
                    return ClientResponse(**response.json())
                elif response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Client {cliente_id} not found"
                    )
                elif response.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only administrators can assign sellers"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error assigning seller"
                    )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling client service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Client service temporarily unavailable"
            )


def get_client_service() -> ClientService:
    """Dependency to get ClientService instance."""
    return ClientService(client_service_url=settings.client_url)
```

### 3.3 BFF Controller
```python
# bff/common/clients/controller.py

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .schemas import (
    ClientCreateRequest,
    ClientUpdateRequest,
    AssignSellerRequest,
    ClientResponse,
    ClientListResponse
)
from .client_service import ClientService, get_client_service
from common.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["clients"])
security = HTTPBearer()


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create client profile",
    description="Create a new client profile. Only client users can create their profile after signup.",
    responses={
        201: {"description": "Client created successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Client users only"},
        409: {"description": "Client already exists"},
        503: {"description": "Client service unavailable"},
    }
)
async def create_client(
    request: ClientCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    """Create a new client profile."""

    logger.info(f"Creating client profile for user: {current_user.get('email')}")

    # Validate user is a client user
    user_groups = current_user.get("cognito:groups", [])
    if "client_users" not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only client users can create client profiles"
        )

    return await client_service.create_client(
        request=request,
        access_token=credentials.credentials
    )


@router.get(
    "/me",
    response_model=ClientResponse,
    summary="Get my client profile",
    description="Get the authenticated client user's profile.",
    responses={
        200: {"description": "Client profile retrieved successfully"},
        404: {"description": "Client profile not found"},
        401: {"description": "Unauthorized"},
        503: {"description": "Client service unavailable"},
    }
)
async def get_my_client_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    """Get current authenticated client's profile."""

    logger.info(f"Getting profile for user: {current_user.get('email')}")

    return await client_service.get_my_profile(
        access_token=credentials.credentials
    )


@router.get(
    "/{cliente_id}",
    response_model=ClientResponse,
    summary="Get client by ID",
    description="Get a specific client by ID. Web users only.",
    responses={
        200: {"description": "Client retrieved successfully"},
        404: {"description": "Client not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Web users only"},
        503: {"description": "Client service unavailable"},
    }
)
async def get_client(
    cliente_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    """Get a client by ID."""

    logger.info(f"Getting client {cliente_id} by user: {current_user.get('email')}")

    # Validate user is a web user
    user_groups = current_user.get("cognito:groups", [])
    if "web_users" not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only web users can view client details"
        )

    return await client_service.get_client(
        cliente_id=cliente_id,
        access_token=credentials.credentials
    )


@router.get(
    "",
    response_model=ClientListResponse,
    summary="List all clients",
    description="List all clients with pagination. Web users only.",
    responses={
        200: {"description": "Clients retrieved successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Web users only"},
        503: {"description": "Client service unavailable"},
    }
)
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    """List all clients with pagination."""

    logger.info(f"Listing clients by user: {current_user.get('email')}")

    # Validate user is a web user
    user_groups = current_user.get("cognito:groups", [])
    if "web_users" not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only web users can list clients"
        )

    return await client_service.list_clients(
        skip=skip,
        limit=limit,
        access_token=credentials.credentials
    )


@router.put(
    "/{cliente_id}",
    response_model=ClientResponse,
    summary="Update client",
    description="Update a client. Client users can update their own profile. Web users can update any client.",
    responses={
        200: {"description": "Client updated successfully"},
        404: {"description": "Client not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        503: {"description": "Client service unavailable"},
    }
)
async def update_client(
    cliente_id: str,
    request: ClientUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    """Update a client."""

    logger.info(f"Updating client {cliente_id} by user: {current_user.get('email')}")

    return await client_service.update_client(
        cliente_id=cliente_id,
        request=request,
        access_token=credentials.credentials
    )


@router.patch(
    "/{cliente_id}/assign-seller",
    response_model=ClientResponse,
    summary="Assign seller to client",
    description="Assign or unassign a seller to a client. Web users (administrators) only.",
    responses={
        200: {"description": "Seller assigned successfully"},
        404: {"description": "Client not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Web users only"},
        503: {"description": "Client service unavailable"},
    }
)
async def assign_seller_to_client(
    cliente_id: str,
    request: AssignSellerRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    """Assign or unassign a seller to a client."""

    logger.info(f"Assigning seller to client {cliente_id} by user: {current_user.get('email')}")

    # Validate user is a web user (administrator)
    user_groups = current_user.get("cognito:groups", [])
    if "web_users" not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can assign sellers to clients"
        )

    return await client_service.assign_seller(
        cliente_id=cliente_id,
        request=request,
        access_token=credentials.credentials
    )
```

### 3.4 Register BFF Routes
```python
# bff/app.py

from common.clients.controller import router as clients_router

# Add to existing routers
app.include_router(clients_router, prefix="/bff")
```

---

## 4. Unit Tests

### 4.1 Client Microservice Tests

#### Domain Tests
```python
# client/tests/domain/test_client_entity.py

import pytest
from datetime import datetime
from src.domain.entities.client import Client

class TestClientEntity:
    """Tests for Client entity."""

    def test_create_client_with_valid_data(self):
        """Test creating a client with valid data."""
        client = Client(
            cliente_id="client-123",
            cognito_user_id="cognito-456",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez",
            vendedor_asignado_id="seller-789"
        )

        assert client.cliente_id == "client-123"
        assert client.email == "hospital@example.com"
        assert client.tipo_institucion == "hospital"

    def test_create_client_with_invalid_tipo_institucion(self):
        """Test creating a client with invalid tipo_institucion raises error."""
        with pytest.raises(ValueError, match="Invalid tipo_institucion"):
            Client(
                cliente_id="client-123",
                cognito_user_id="cognito-456",
                email="hospital@example.com",
                telefono="+57-1-234-5678",
                nombre_institucion="Hospital General",
                tipo_institucion="invalid_type",
                nit="900123456-7",
                direccion="Calle 123 #45-67",
                ciudad="Bogotá",
                pais="Colombia",
                representante="Dr. Juan Pérez"
            )

    def test_create_client_without_seller(self):
        """Test creating a client without assigned seller."""
        client = Client(
            cliente_id="client-123",
            cognito_user_id="cognito-456",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        assert client.vendedor_asignado_id is None
```

#### Value Object Tests
```python
# client/tests/domain/test_value_objects.py

import pytest
from src.domain.value_objects import Email, Telefono

class TestEmailValueObject:
    """Tests for Email value object."""

    def test_valid_email(self):
        """Test creating Email with valid email."""
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_invalid_email_format(self):
        """Test creating Email with invalid format raises error."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")

    def test_email_without_domain(self):
        """Test creating Email without domain raises error."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("user@")

class TestTelefonoValueObject:
    """Tests for Telefono value object."""

    def test_valid_telefono_with_country_code(self):
        """Test creating Telefono with country code."""
        telefono = Telefono("+57-1-234-5678")
        assert telefono.value == "+57-1-234-5678"

    def test_valid_telefono_without_country_code(self):
        """Test creating Telefono without country code."""
        telefono = Telefono("1234567890")
        assert telefono.value == "1234567890"

    def test_invalid_telefono_with_letters(self):
        """Test creating Telefono with letters raises error."""
        with pytest.raises(ValueError, match="Invalid phone format"):
            Telefono("123-ABC-4567")
```

#### Use Case Tests
```python
# client/tests/application/test_create_client_use_case.py

import pytest
from unittest.mock import AsyncMock, Mock
from src.application.use_cases.create_client import CreateClientUseCase, CreateClientCommand
from src.domain.entities.client import Client

@pytest.mark.asyncio
class TestCreateClientUseCase:
    """Tests for CreateClientUseCase."""

    async def test_create_client_success(self):
        """Test successfully creating a client."""
        # Arrange
        mock_repository = Mock()
        mock_repository.get_by_email = AsyncMock(return_value=None)
        mock_repository.get_by_cognito_user_id = AsyncMock(return_value=None)
        mock_repository.create = AsyncMock(return_value=Client(
            cliente_id="client-123",
            cognito_user_id="cognito-456",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        ))

        use_case = CreateClientUseCase(mock_repository)
        command = CreateClientCommand(
            cognito_user_id="cognito-456",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.cliente_id == "client-123"
        assert result.email == "hospital@example.com"
        mock_repository.get_by_email.assert_awaited_once()
        mock_repository.get_by_cognito_user_id.assert_awaited_once()
        mock_repository.create.assert_awaited_once()

    async def test_create_client_duplicate_email(self):
        """Test creating client with duplicate email raises error."""
        # Arrange
        existing_client = Client(
            cliente_id="existing-123",
            cognito_user_id="cognito-789",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Existing Hospital",
            tipo_institucion="hospital",
            nit="900111222-3",
            direccion="Calle 456",
            ciudad="Cali",
            pais="Colombia",
            representante="Dr. Maria"
        )

        mock_repository = Mock()
        mock_repository.get_by_email = AsyncMock(return_value=existing_client)

        use_case = CreateClientUseCase(mock_repository)
        command = CreateClientCommand(
            cognito_user_id="cognito-456",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(command)

    async def test_create_client_duplicate_cognito_user_id(self):
        """Test creating client with duplicate cognito_user_id raises error."""
        # Arrange
        existing_client = Client(
            cliente_id="existing-123",
            cognito_user_id="cognito-456",
            email="other@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Existing Hospital",
            tipo_institucion="hospital",
            nit="900111222-3",
            direccion="Calle 456",
            ciudad="Cali",
            pais="Colombia",
            representante="Dr. Maria"
        )

        mock_repository = Mock()
        mock_repository.get_by_email = AsyncMock(return_value=None)
        mock_repository.get_by_cognito_user_id = AsyncMock(return_value=existing_client)

        use_case = CreateClientUseCase(mock_repository)
        command = CreateClientCommand(
            cognito_user_id="cognito-456",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(command)

    async def test_create_client_invalid_email_format(self):
        """Test creating client with invalid email raises error."""
        # Arrange
        mock_repository = Mock()
        mock_repository.get_by_email = AsyncMock(return_value=None)
        mock_repository.get_by_cognito_user_id = AsyncMock(return_value=None)

        use_case = CreateClientUseCase(mock_repository)
        command = CreateClientCommand(
            cognito_user_id="cognito-456",
            email="invalid-email",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            await use_case.execute(command)
```

#### Controller Tests
```python
# client/tests/infrastructure/api/test_client_controller.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch
from src.infrastructure.api.app import app

client = TestClient(app)

@pytest.fixture
def mock_auth():
    """Mock authentication."""
    with patch("src.infrastructure.api.dependencies.get_current_user") as mock:
        mock.return_value = {
            "sub": "cognito-user-123",
            "email": "user@example.com",
            "cognito:groups": ["client_users"]
        }
        yield mock

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    with patch("src.infrastructure.api.dependencies.get_db_session") as mock:
        yield mock

class TestCreateClientEndpoint:
    """Tests for POST /clients endpoint."""

    def test_create_client_success(self, mock_auth, mock_db_session):
        """Test successfully creating a client."""
        # Arrange
        request_data = {
            "email": "hospital@example.com",
            "telefono": "+57-1-234-5678",
            "nombre_institucion": "Hospital General",
            "tipo_institucion": "hospital",
            "nit": "900123456-7",
            "direccion": "Calle 123 #45-67",
            "ciudad": "Bogotá",
            "pais": "Colombia",
            "representante": "Dr. Juan Pérez"
        }

        # Act
        response = client.post(
            "/clients",
            json=request_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "hospital@example.com"
        assert data["nombre_institucion"] == "Hospital General"

    def test_create_client_forbidden_for_non_client_users(self, mock_db_session):
        """Test that non-client users cannot create clients."""
        # Arrange
        with patch("src.infrastructure.api.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "sub": "cognito-user-123",
                "email": "admin@example.com",
                "cognito:groups": ["web_users"]
            }

            request_data = {
                "email": "hospital@example.com",
                "telefono": "+57-1-234-5678",
                "nombre_institucion": "Hospital General",
                "tipo_institucion": "hospital",
                "nit": "900123456-7",
                "direccion": "Calle 123 #45-67",
                "ciudad": "Bogotá",
                "pais": "Colombia",
                "representante": "Dr. Juan Pérez"
            }

            # Act
            response = client.post(
                "/clients",
                json=request_data,
                headers={"Authorization": "Bearer fake-token"}
            )

            # Assert
            assert response.status_code == 403
            assert "client users" in response.json()["detail"].lower()

    def test_create_client_invalid_email(self, mock_auth, mock_db_session):
        """Test creating client with invalid email returns 422."""
        # Arrange
        request_data = {
            "email": "invalid-email",
            "telefono": "+57-1-234-5678",
            "nombre_institucion": "Hospital General",
            "tipo_institucion": "hospital",
            "nit": "900123456-7",
            "direccion": "Calle 123 #45-67",
            "ciudad": "Bogotá",
            "pais": "Colombia",
            "representante": "Dr. Juan Pérez"
        }

        # Act
        response = client.post(
            "/clients",
            json=request_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 422

class TestGetMyClientProfileEndpoint:
    """Tests for GET /clients/me endpoint."""

    def test_get_my_profile_success(self, mock_auth, mock_db_session):
        """Test successfully getting own profile."""
        # Act
        response = client.get(
            "/clients/me",
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "cliente_id" in data
        assert "email" in data

    def test_get_my_profile_not_found(self, mock_auth, mock_db_session):
        """Test getting profile when it doesn't exist."""
        # Mock repository to return None
        with patch("src.infrastructure.repositories.sqlalchemy_client_repository.SQLAlchemyClientRepository.get_by_cognito_user_id") as mock:
            mock.return_value = None

            # Act
            response = client.get(
                "/clients/me",
                headers={"Authorization": "Bearer fake-token"}
            )

            # Assert
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

class TestAssignSellerEndpoint:
    """Tests for PATCH /clients/{cliente_id}/assign-seller endpoint."""

    def test_assign_seller_success(self, mock_db_session):
        """Test successfully assigning a seller."""
        # Arrange
        with patch("src.infrastructure.api.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "sub": "cognito-admin-123",
                "email": "admin@example.com",
                "cognito:groups": ["web_users"]
            }

            request_data = {
                "vendedor_asignado_id": "seller-123"
            }

            # Act
            response = client.patch(
                "/clients/client-456/assign-seller",
                json=request_data,
                headers={"Authorization": "Bearer fake-token"}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["vendedor_asignado_id"] == "seller-123"

    def test_assign_seller_forbidden_for_non_admin(self, mock_auth, mock_db_session):
        """Test that non-admins cannot assign sellers."""
        # client_users in mock_auth fixture

        request_data = {
            "vendedor_asignado_id": "seller-123"
        }

        # Act
        response = client.patch(
            "/clients/client-456/assign-seller",
            json=request_data,
            headers={"Authorization": "Bearer fake-token"}
        )

        # Assert
        assert response.status_code == 403
        assert "administrator" in response.json()["detail"].lower()
```

### 4.2 BFF Tests

#### Service Tests
```python
# bff/tests/common/clients/test_client_service.py

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
import httpx

from common.clients.client_service import ClientService
from common.clients.schemas import ClientCreateRequest, ClientResponse

@pytest.mark.asyncio
class TestClientService:
    """Tests for ClientService."""

    async def test_create_client_success(self):
        """Test successfully creating a client."""
        # Arrange
        service = ClientService("http://client-service:8000")
        request = ClientCreateRequest(
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "cliente_id": "client-123",
            "cognito_user_id": "cognito-456",
            "email": "hospital@example.com",
            "telefono": "+57-1-234-5678",
            "nombre_institucion": "Hospital General",
            "tipo_institucion": "hospital",
            "nit": "900123456-7",
            "direccion": "Calle 123 #45-67",
            "ciudad": "Bogotá",
            "pais": "Colombia",
            "representante": "Dr. Juan Pérez",
            "vendedor_asignado_id": None,
            "creado_en": "2024-01-01T00:00:00",
            "actualizado_en": "2024-01-01T00:00:00"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # Act
            result = await service.create_client(request, "fake-token")

            # Assert
            assert result.cliente_id == "client-123"
            assert result.email == "hospital@example.com"

    async def test_create_client_duplicate(self):
        """Test creating duplicate client returns 409."""
        # Arrange
        service = ClientService("http://client-service:8000")
        request = ClientCreateRequest(
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.json.return_value = {
            "detail": "Client already exists"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await service.create_client(request, "fake-token")

            assert exc_info.value.status_code == 409

    async def test_create_client_service_unavailable(self):
        """Test service unavailable returns 503."""
        # Arrange
        service = ClientService("http://client-service:8000")
        request = ClientCreateRequest(
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ConnectTimeout("Connection timeout")
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await service.create_client(request, "fake-token")

            assert exc_info.value.status_code == 503

    async def test_get_my_profile_success(self):
        """Test successfully getting own profile."""
        # Arrange
        service = ClientService("http://client-service:8000")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cliente_id": "client-123",
            "cognito_user_id": "cognito-456",
            "email": "hospital@example.com",
            "telefono": "+57-1-234-5678",
            "nombre_institucion": "Hospital General",
            "tipo_institucion": "hospital",
            "nit": "900123456-7",
            "direccion": "Calle 123 #45-67",
            "ciudad": "Bogotá",
            "pais": "Colombia",
            "representante": "Dr. Juan Pérez",
            "vendedor_asignado_id": None,
            "creado_en": "2024-01-01T00:00:00",
            "actualizado_en": "2024-01-01T00:00:00"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Act
            result = await service.get_my_profile("fake-token")

            # Assert
            assert result.cliente_id == "client-123"
            assert result.email == "hospital@example.com"

    async def test_get_my_profile_not_found(self):
        """Test getting profile when it doesn't exist."""
        # Arrange
        service = ClientService("http://client-service:8000")

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": "Client profile not found"
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await service.get_my_profile("fake-token")

            assert exc_info.value.status_code == 404
```

#### Controller Tests
```python
# bff/tests/common/clients/test_controller.py

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException

from common.clients.controller import create_client, get_my_client_profile
from common.clients.schemas import ClientCreateRequest, ClientResponse

@pytest.fixture
def mock_client_service():
    """Mock ClientService."""
    return Mock()

@pytest.fixture
def mock_credentials():
    """Mock HTTPAuthorizationCredentials."""
    mock = Mock()
    mock.credentials = "fake-access-token"
    return mock

@pytest.fixture
def mock_current_user_client():
    """Mock current user with client_users group."""
    return {
        "sub": "cognito-user-123",
        "email": "user@example.com",
        "cognito:groups": ["client_users"]
    }

@pytest.fixture
def mock_current_user_web():
    """Mock current user with web_users group."""
    return {
        "sub": "cognito-admin-123",
        "email": "admin@example.com",
        "cognito:groups": ["web_users"]
    }

@pytest.mark.asyncio
class TestCreateClientController:
    """Tests for create_client controller."""

    async def test_create_client_success(
        self,
        mock_client_service,
        mock_credentials,
        mock_current_user_client
    ):
        """Test successfully creating a client."""
        # Arrange
        request = ClientCreateRequest(
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        expected_response = ClientResponse(
            cliente_id="client-123",
            cognito_user_id="cognito-user-123",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez",
            vendedor_asignado_id=None,
            creado_en="2024-01-01T00:00:00",
            actualizado_en="2024-01-01T00:00:00"
        )

        mock_client_service.create_client = AsyncMock(return_value=expected_response)

        # Act
        result = await create_client(
            request=request,
            credentials=mock_credentials,
            current_user=mock_current_user_client,
            client_service=mock_client_service
        )

        # Assert
        assert result.cliente_id == "client-123"
        assert result.email == "hospital@example.com"
        mock_client_service.create_client.assert_awaited_once()

    async def test_create_client_forbidden_for_non_client_user(
        self,
        mock_client_service,
        mock_credentials,
        mock_current_user_web
    ):
        """Test creating client forbidden for non-client users."""
        # Arrange
        request = ClientCreateRequest(
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_client(
                request=request,
                credentials=mock_credentials,
                current_user=mock_current_user_web,
                client_service=mock_client_service
            )

        assert exc_info.value.status_code == 403
        assert "client users" in exc_info.value.detail.lower()

@pytest.mark.asyncio
class TestGetMyClientProfileController:
    """Tests for get_my_client_profile controller."""

    async def test_get_my_profile_success(
        self,
        mock_client_service,
        mock_credentials,
        mock_current_user_client
    ):
        """Test successfully getting own profile."""
        # Arrange
        expected_response = ClientResponse(
            cliente_id="client-123",
            cognito_user_id="cognito-user-123",
            email="hospital@example.com",
            telefono="+57-1-234-5678",
            nombre_institucion="Hospital General",
            tipo_institucion="hospital",
            nit="900123456-7",
            direccion="Calle 123 #45-67",
            ciudad="Bogotá",
            pais="Colombia",
            representante="Dr. Juan Pérez",
            vendedor_asignado_id=None,
            creado_en="2024-01-01T00:00:00",
            actualizado_en="2024-01-01T00:00:00"
        )

        mock_client_service.get_my_profile = AsyncMock(return_value=expected_response)

        # Act
        result = await get_my_client_profile(
            credentials=mock_credentials,
            current_user=mock_current_user_client,
            client_service=mock_client_service
        )

        # Assert
        assert result.cliente_id == "client-123"
        assert result.email == "hospital@example.com"
        mock_client_service.get_my_profile.assert_awaited_once()
```

---

## 5. Implementation Steps

### Phase 1: Client Microservice (Week 1)
1. Create database migration for new fields
2. Implement domain entities and value objects
3. Implement repository interface and SQLAlchemy implementation
4. Implement use cases (create, update, assign seller)
5. Write unit tests for domain, use cases, and repository
6. Implement API controllers
7. Write integration tests

### Phase 2: BFF Layer (Week 2)
1. Implement BFF schemas
2. Implement ClientService for microservice communication
3. Implement BFF controllers
4. Write unit tests for service and controllers
5. Update BFF configuration for CLIENT_URL
6. Test end-to-end flow

### Phase 3: Testing & Documentation (Week 3)
1. Run all unit tests
2. Run integration tests
3. Test with Postman/curl
4. Update API documentation
5. Create user guide for client creation flow

---

## 6. Testing Checklist

### Unit Tests
- [ ] Domain entities validation
- [ ] Value objects validation
- [ ] Use case business logic
- [ ] Repository CRUD operations
- [ ] Controller request/response handling
- [ ] BFF service HTTP communication
- [ ] BFF controller authorization

### Integration Tests
- [ ] Database migrations
- [ ] API endpoints (POST, GET, PUT, PATCH)
- [ ] Authentication flow
- [ ] Authorization checks (user groups)
- [ ] BFF to microservice communication

### Manual Testing
- [ ] Client signup and profile creation
- [ ] Client profile retrieval
- [ ] Client profile update
- [ ] Seller assignment by admin
- [ ] Access control (client vs web users)
- [ ] Error handling

---

## 7. Configuration

### Environment Variables

#### BFF (.env)
```env
CLIENT_URL=http://client:8002/client
```

#### Client Microservice (.env)
```env
DATABASE_URL=postgresql://postgres:password@client-db:5432/client
```

---

## 8. API Endpoints Summary

### BFF Endpoints
```
POST   /bff/clients                    - Create client (client_users only)
GET    /bff/clients/me                 - Get own profile (authenticated)
GET    /bff/clients/{id}               - Get client by ID (web_users only)
GET    /bff/clients                    - List all clients (web_users only)
PUT    /bff/clients/{id}               - Update client
PATCH  /bff/clients/{id}/assign-seller - Assign seller (web_users only)
```

### Client Microservice Endpoints
```
POST   /client/clients                    - Create client
GET    /client/clients/me                 - Get own profile
GET    /client/clients/{id}               - Get client by ID
GET    /client/clients                    - List all clients
PUT    /client/clients/{id}               - Update client
PATCH  /client/clients/{id}/assign-seller - Assign seller
```

---

## 9. Authorization Matrix

| Endpoint | client_users | seller_users | web_users |
|----------|--------------|--------------|-----------|
| POST /clients | ✅ Own profile | ❌ | ❌ |
| GET /clients/me | ✅ Own | ✅ Own | ✅ Own |
| GET /clients/{id} | ❌ | ❌ | ✅ All |
| GET /clients | ❌ | ❌ | ✅ All |
| PUT /clients/{id} | ✅ Own | ❌ | ✅ All |
| PATCH /clients/{id}/assign-seller | ❌ | ❌ | ✅ All |

---

## 10. Success Criteria

1. ✅ All unit tests passing (>90% coverage)
2. ✅ All integration tests passing
3. ✅ Client can create profile after signup
4. ✅ Client can view/update own profile
5. ✅ Web users can manage all clients
6. ✅ Web users can assign sellers to clients
7. ✅ Proper authorization enforced
8. ✅ API documentation updated
9. ✅ Error handling comprehensive
10. ✅ Logging implemented
