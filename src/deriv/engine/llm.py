from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from deriv.core.config import settings
from deriv.engine.schemas import LLMCallLog

T = TypeVar("T", bound=BaseModel)

_client = None

def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.gapgpt.app/v1",
        )
    return _client

def generate_structured_output(
    system_prompt: str,
    user_prompt: str,
    response_model: Type[T],
    stage: str,
    input_artifacts: list[str],
    output_artifact: str,
    state: dict[str, Any],
) -> T:
    """
    Calls the LLM, instructs it to output JSON matching the Pydantic model,
    parses it, and appends a log entry to the state.
    """
    client = get_openai_client()
    
    # Instruct model to output JSON that matches the schema
    schema_json = response_model.model_json_schema()
    full_system_prompt = (
        f"{system_prompt}\n\n"
        "You must respond with valid JSON ONLY. "
        "The JSON object must strictly match the following JSON Schema:\n"
        f"{json.dumps(schema_json, indent=2)}"
    )

    messages = [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Combine prompts to create a hash
    full_prompt_text = full_system_prompt + "\n" + user_prompt
    prompt_hash = hashlib.sha256(full_prompt_text.encode("utf-8")).hexdigest()

    response = client.chat.completions.create(
        model=settings.DEFAULT_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    response_text = response.choices[0].message.content or "{}"
    parsed_model = response_model.model_validate_json(response_text)

    # Log the call
    log_entry = LLMCallLog(
        stage=stage,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        provider="openai-compatible",
        model=settings.DEFAULT_MODEL,
        prompt_hash=prompt_hash,
        input_artifacts=input_artifacts,
        output_artifact=output_artifact,
    )
    
    if "llm_logs" not in state:
        state["llm_logs"] = []
    state["llm_logs"].append(log_entry.model_dump())

    return parsed_model
