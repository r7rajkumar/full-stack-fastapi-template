import os
import json
from typing import Any
from fastapi import APIRouter, HTTPException
from sqlmodel import SQLModel
import httpx

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentQuestion(SQLModel):
    question: str


class AgentResponse(SQLModel):
    answer: str
    policies_consulted: list[dict] = []

def get_internal_token() -> str:
    from app.core.security import create_access_token
    from app.core.config import settings
    from app.core.db import engine
    from app.models import User
    from sqlmodel import Session, select
    from datetime import timedelta
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        ).first()
        if not user:
            raise Exception("Superuser not found")
        return create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=5)
        )

def search_policies_internal(query: str, k: int, auth_token: str) -> list[dict]:
    resp = httpx.get(
        "http://backend:8000/api/v1/policies/search/semantic",
        params={"q": query, "k": k},
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=30.0
    )
    resp.raise_for_status()
    return resp.json()


def get_client_internal(client_id: int, auth_token: str) -> dict:
    resp = httpx.get(
        f"http://backend:8000/api/v1/clients/{client_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=10.0
    )
    resp.raise_for_status()
    return resp.json()


SYSTEM_PROMPT = """You are an expert insurance broker assistant for New Zealand businesses.
Your job is to recommend the most suitable insurance policies for clients based on their
industry, size, turnover, and risk profile.

When answering questions:
1. Always search for relevant policies before answering.
2. Explain WHY each recommended policy suits the client.
3. Reference specific coverage details from the policy descriptions.
4. Always mention the insurer and sum insured for each recommendation.
"""

TOOLS = [
    {
        "name": "search_policies_semantic",
        "description": "Search insurance policies using semantic similarity. Use this to find policies relevant to a client's needs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language description of coverage needed"
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return, default 5"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_client",
        "description": "Get details about a specific client by their numeric ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "The numeric ID of the client"
                }
            },
            "required": ["client_id"]
        }
    }
]


@router.post("/ask", response_model=AgentResponse)
def agent_ask(question_in: AgentQuestion) -> Any:
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    client = genai.Client(api_key=api_key)
    internal_token = get_internal_token()
    policies_consulted = []

    # Build messages history
    messages = [
        types.Content(
            role="user",
            parts=[types.Part(text=question_in.question)]
        )
    ]

    for _ in range(5):
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[types.Tool(function_declarations=TOOLS)],
            )
        )

        candidate = response.candidates[0]

        # Check if there are function calls
        function_calls = [
            part for part in candidate.content.parts
            if part.function_call is not None
        ]

        if not function_calls:
            # No function calls — final answer
            answer = response.text or "No answer generated."
            return AgentResponse(
                answer=answer,
                policies_consulted=policies_consulted
            )

        # Add assistant response to history
        messages.append(candidate.content)

        # Process each function call
        tool_response_parts = []
        for part in function_calls:
            fn_name = part.function_call.name
            fn_args = dict(part.function_call.args)

            if fn_name == "search_policies_semantic":
                query = fn_args.get("query", question_in.question)
                k = int(fn_args.get("k", 5))
                result = search_policies_internal(query, k, internal_token)
                policies_consulted.extend(result)
                result_str = json.dumps(result)
            elif fn_name == "get_client":
                client_id = int(fn_args.get("client_id", 0))
                result = get_client_internal(client_id, internal_token)
                result_str = json.dumps(result)
            else:
                result_str = json.dumps({"error": f"Unknown function: {fn_name}"})

            tool_response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fn_name,
                        response={"result": result_str}
                    )
                )
            )

        # Add tool results to history
        messages.append(
            types.Content(
                role="tool",
                parts=tool_response_parts
            )
        )

    # Fallback
    return AgentResponse(
        answer="Agent reached maximum iterations.",
        policies_consulted=policies_consulted
    )