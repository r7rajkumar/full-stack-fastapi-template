from typing import Any
import os
from fastapi import APIRouter, HTTPException
from sqlmodel import select, func, text
from sqlalchemy import cast
from app.api.deps import SessionDep, CurrentUser
from app.models import (
    Policy, PolicyCreate, PolicyUpdate,
    PolicyPublic, PoliciesPublic, PolicyWithScore, Message
)

router = APIRouter(prefix="/policies", tags=["policies"])


def get_embedding(text_input: str) -> list[float]:
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text_input
    )
    return result.embeddings[0].values



@router.get("/", response_model=PoliciesPublic)
def read_policies(session: SessionDep, current_user: CurrentUser,
                  skip: int = 0, limit: int = 100) -> Any:
    count = session.exec(select(func.count()).select_from(Policy)).one()
    policies = session.exec(select(Policy).offset(skip).limit(limit)).all()
    return PoliciesPublic(data=policies, count=count)


@router.get("/search/semantic", response_model=list[PolicyWithScore])
def semantic_search(session: SessionDep, current_user: CurrentUser,
                    q: str, k: int = 5) -> Any:
    """Search policies using cosine similarity on embeddings."""
    query_embedding = get_embedding(q)
    vec_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    # Use pgvector <=> operator for cosine distance

    sql = text("""
        SELECT id, product_type, insurer, sum_insured_nzd, description,
              (embedding::vector <=> CAST(:vec AS vector)) AS score
        FROM policy
        WHERE embedding IS NOT NULL
        ORDER BY score ASC
        LIMIT :k
    """)
    rows = session.exec(sql, params={"vec": vec_str, "k": k}).all()

    result = []
    for row in rows:
        result.append(PolicyWithScore(
            id=row.id,
            product_type=row.product_type,
            insurer=row.insurer,
            sum_insured_nzd=row.sum_insured_nzd,
            description=row.description,
            score=row.score,
        ))
    return result

@router.post("/reindex")
def reindex_policies(session: SessionDep, current_user: CurrentUser) -> Any:
    """Generate and store embeddings for all policies."""
    policies = session.exec(select(Policy)).all()
    updated = 0
    for policy in policies:
        embedding = get_embedding(policy.description)
        vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
        session.exec(
            text("UPDATE policy SET embedding = :vec WHERE id = :id"),
            params={"vec": vec_str, "id": policy.id}
        )
        updated += 1
    session.commit()
    return {"message": f"Reindexed {updated} policies"}

@router.get("/{id}", response_model=PolicyPublic)
def read_policy(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    policy = session.get(Policy, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/", response_model=PolicyPublic)
def create_policy(*, session: SessionDep, current_user: CurrentUser,
                  policy_in: PolicyCreate) -> Any:
    policy = Policy.model_validate(policy_in)
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


@router.put("/{id}", response_model=PolicyPublic)
def update_policy(*, session: SessionDep, current_user: CurrentUser,
                  id: int, policy_in: PolicyUpdate) -> Any:
    policy = session.get(Policy, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.sqlmodel_update(policy_in.model_dump(exclude_unset=True))
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


@router.delete("/{id}")
def delete_policy(session: SessionDep, current_user: CurrentUser, id: int) -> Message:
    policy = session.get(Policy, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    session.delete(policy)
    session.commit()
    return Message(message="Policy deleted successfully")