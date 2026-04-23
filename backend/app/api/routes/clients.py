from typing import Any
from fastapi import APIRouter, HTTPException
from sqlmodel import select, func
from app.api.deps import SessionDep, CurrentUser
from app.models import (
    Client, ClientCreate, ClientUpdate,
    ClientPublic, ClientsPublic, Message
)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=ClientsPublic)
def read_clients(session: SessionDep, current_user: CurrentUser,
                 skip: int = 0, limit: int = 100) -> Any:
    count = session.exec(select(func.count()).select_from(Client)).one()
    clients = session.exec(select(Client).offset(skip).limit(limit)).all()
    return ClientsPublic(data=clients, count=count)


@router.get("/{id}", response_model=ClientPublic)
def read_client(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    client = session.get(Client, id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("/", response_model=ClientPublic)
def create_client(*, session: SessionDep, current_user: CurrentUser,
                  client_in: ClientCreate) -> Any:
    client = Client.model_validate(client_in)
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.put("/{id}", response_model=ClientPublic)
def update_client(*, session: SessionDep, current_user: CurrentUser,
                  id: int, client_in: ClientUpdate) -> Any:
    client = session.get(Client, id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.sqlmodel_update(client_in.model_dump(exclude_unset=True))
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.delete("/{id}")
def delete_client(session: SessionDep, current_user: CurrentUser, id: int) -> Message:
    client = session.get(Client, id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    session.delete(client)
    session.commit()
    return Message(message="Client deleted successfully")