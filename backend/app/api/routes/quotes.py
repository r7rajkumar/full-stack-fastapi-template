from typing import Any
from fastapi import APIRouter, HTTPException
from sqlmodel import select, func
from app.api.deps import SessionDep, CurrentUser
from app.models import (
    Quote, QuoteCreate, QuoteUpdate,
    QuotePublic, QuotesPublic, Message
)

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/", response_model=QuotesPublic)
def read_quotes(session: SessionDep, current_user: CurrentUser,
                skip: int = 0, limit: int = 100) -> Any:
    count = session.exec(select(func.count()).select_from(Quote)).one()
    quotes = session.exec(select(Quote).offset(skip).limit(limit)).all()
    return QuotesPublic(data=quotes, count=count)


@router.get("/{id}", response_model=QuotePublic)
def read_quote(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    quote = session.get(Quote, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.post("/", response_model=QuotePublic)
def create_quote(*, session: SessionDep, current_user: CurrentUser,
                 quote_in: QuoteCreate) -> Any:
    quote = Quote.model_validate(quote_in)
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.put("/{id}", response_model=QuotePublic)
def update_quote(*, session: SessionDep, current_user: CurrentUser,
                 id: int, quote_in: QuoteUpdate) -> Any:
    quote = session.get(Quote, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote.sqlmodel_update(quote_in.model_dump(exclude_unset=True))
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.delete("/{id}")
def delete_quote(session: SessionDep, current_user: CurrentUser, id: int) -> Message:
    quote = session.get(Quote, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    session.delete(quote)
    session.commit()
    return Message(message="Quote deleted successfully")