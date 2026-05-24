"""
Integration smoke test for the Case Conversation Workflow.
Uses FastAPI TestClient to avoid a live server dependency.
"""

# Integration test module: this suite runs in-process with TestClient,
# so no external live API server is needed.

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


PASS = "\033[92mOK\033[0m"
FAIL = "\033[91mFAIL\033[0m"
INFO = "\033[94mINFO\033[0m"


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label}" + (f"  [{detail}]" if detail else ""))
    return condition


def section(title: str):
    print(f"\n{'-' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}")


@pytest.fixture(scope="function")
def client():
    with patch("app.main.init_db", new_callable=AsyncMock), \
         patch("app.main.close_db", new_callable=AsyncMock), \
         patch("app.main.faiss_manager") as mock_faiss:
        mock_faiss.rebuild = AsyncMock()
        mock_faiss.size = 0
        from app.main import app
        from app.config import get_settings
        get_settings().api_key = "test-key"
        with TestClient(app) as c:
            yield c


@pytest.fixture(scope="function")
def api_base_path() -> str:
    return os.getenv("DALEEL_TEST_BASE_PATH", "/api/v1")


@pytest.fixture(scope="function")
def api_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("DALEEL_API_KEY", "test-key").strip()
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


@pytest.fixture(scope="function")
def mock_case_backend(monkeypatch):
    from app.services import case_conversation_service

    now = datetime.now(timezone.utc)
    case_id = "test-case-001"

    initial_context = {
        "title": "Non-conformite contrats de travail - SARL Tunis",
        "facts_known": [
            "L'entreprise est une SARL basee a Tunis",
            "3 employes travaillent sans contrat ecrit",
            "L'entreprise opere dans le secteur textile",
        ],
        "facts_missing": [
            "Duree d'emploi des salaries sans contrat",
            "Existence d'un reglement interieur",
            "Nombre total de salaries",
        ],
        "matter_type": "labour_compliance",
        "urgency": "high",
        "article_references": ["Art. 6 du Code du Travail"],
        "next_question": "Depuis combien de temps ces employes travaillent-ils sans contrat signe ?",
    }

    followup_context = {
        "title": "Non-conformite contrats de travail - SARL Tunis",
        "facts_known": [
            "L'entreprise est une SARL basee a Tunis",
            "3 employes travaillent sans contrat ecrit",
            "L'entreprise opere dans le secteur textile",
            "Les 3 employes travaillent depuis 8 mois",
            "L'entreprise n'a pas encore de reglement interieur",
        ],
        "facts_missing": [
            "Nombre total de salaries",
        ],
        "matter_type": "labour_compliance",
        "urgency": "high",
        "article_references": ["Art. 6 du Code du Travail"],
        "next_question": "Quel est le nombre total de salaries dans l'entreprise ?",
    }

    state = {
        "case": {
            "id": case_id,
            "title": initial_context["title"],
            "description": "",
            "company_profile_id": None,
            "status": "in_progress",
            "priority": "high",
            "assigned_to": None,
            "tags": ["conversation", "labour_compliance"],
            "created_by": "test_user",
            "created_at": now,
            "updated_at": now,
            "closed_at": None,
            "message_count": 4,
            "document_count": 0,
            "finding_count": 0,
            "action_count": 0,
        },
        "messages": [],
        "context": dict(initial_context),
        "next_msg_id": 1,
    }

    async def fake_extract_context_from_conversation(conversation, detected_lang):
        user_turns = sum(1 for msg in conversation if msg.get("role") == "user")
        return dict(followup_context if user_turns > 1 else initial_context)

    async def fake_create_case(db, **kwargs):
        state["case"]["title"] = kwargs.get("title") or state["case"]["title"]
        state["case"]["description"] = kwargs.get("description") or state["case"]["description"]
        state["case"]["priority"] = kwargs.get("priority") or state["case"]["priority"]
        state["case"]["created_by"] = kwargs.get("created_by") or state["case"]["created_by"]
        return dict(state["case"])

    async def fake_get_case(db, asked_case_id, organization_id=None):
        if asked_case_id != case_id:
            return None
        case_copy = dict(state["case"])
        case_copy["message_count"] = max(4, len(state["messages"]))
        case_copy["updated_at"] = datetime.now(timezone.utc)
        return case_copy

    async def fake_add_message(db, asked_case_id, *, role, content, metadata=None, organization_id=None):
        msg_id = f"msg-{state['next_msg_id']:03d}"
        state["next_msg_id"] += 1
        message = {
            "id": msg_id,
            "case_id": asked_case_id,
            "role": role,
            "content": content,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc),
        }
        state["messages"].append(message)
        return dict(message)

    async def fake_list_messages(db, asked_case_id, skip=0, limit=200, organization_id=None):
        sliced = state["messages"][skip : skip + limit]
        return [dict(m) for m in sliced], len(state["messages"])

    async def fake_update_case(db, asked_case_id, **kwargs):
        state["case"].update(kwargs)
        state["case"]["updated_at"] = datetime.now(timezone.utc)
        return dict(state["case"])

    async def fake_save_conversation_context(asked_case_id, context, organization_id=None):
        saved = dict(context)
        saved["updated_at"] = datetime.now(timezone.utc)
        state["context"] = saved

    async def fake_load_conversation_context(asked_case_id, organization_id=None):
        return dict(state["context"])

    async def fake_log_event(*args, **kwargs):
        return None

    monkeypatch.setattr(
        case_conversation_service,
        "extract_context_from_conversation",
        fake_extract_context_from_conversation,
    )
    monkeypatch.setattr(case_conversation_service.case_service, "create_case", fake_create_case)
    monkeypatch.setattr(case_conversation_service.case_service, "get_case", fake_get_case)
    monkeypatch.setattr(case_conversation_service.case_service, "add_message", fake_add_message)
    monkeypatch.setattr(case_conversation_service.case_service, "list_messages", fake_list_messages)
    monkeypatch.setattr(case_conversation_service.case_service, "update_case", fake_update_case)
    monkeypatch.setattr(case_conversation_service, "_save_conversation_context", fake_save_conversation_context)
    monkeypatch.setattr(case_conversation_service, "_load_conversation_context", fake_load_conversation_context)
    monkeypatch.setattr(case_conversation_service.audit_service, "log_event", fake_log_event)

    return state


@pytest.fixture(scope="function")
def created_case(client: TestClient, api_base_path: str, api_headers: dict, mock_case_backend: dict) -> dict:
    section("1. POST /cases/from-conversation")

    situation = (
        "Notre SARL basee a Tunis emploie 15 personnes. "
        "3 employes travaillent depuis 8 mois sans contrat de travail ecrit. "
        "Nous operons dans le secteur du textile. "
        "L'inspecteur du travail doit effectuer un controle dans 2 semaines."
    )

    resp = client.post(
        f"{api_base_path}/cases/from-conversation",
        json={"situation": situation, "created_by": "test_user"},
        headers=api_headers,
    )

    print(f"  {INFO} Status: {resp.status_code}")
    ok = check("HTTP 201", resp.status_code == 201, f"got {resp.status_code}")
    assert ok

    data = resp.json()
    case_id = data.get("case_id")
    ctx = data.get("context", {})

    print(f"  {INFO} case_id: {case_id}")
    print(f"  {INFO} matter_type: {ctx.get('matter_type')}")
    print(f"  {INFO} urgency: {ctx.get('urgency')}")
    print(f"  {INFO} facts_known ({len(ctx.get('facts_known', []))}): {ctx.get('facts_known')}")
    print(f"  {INFO} facts_missing ({len(ctx.get('facts_missing', []))}): {ctx.get('facts_missing')}")
    print(f"  {INFO} next_question: {ctx.get('next_question')}")
    print(f"  {INFO} article_refs: {ctx.get('article_references')}")

    assert check("case_id present", bool(case_id), "missing case_id")
    assert check("user_message present", bool(data.get("user_message")), "missing user_message")
    assert check("assistant_message present", bool(data.get("assistant_message")), "missing assistant_message")
    assert check("context present", bool(ctx), "missing context")
    assert check(
        "matter_type valid",
        ctx.get("matter_type") in [
            "labour_compliance",
            "corporate_formation",
            "corporate_governance",
            "contract_dispute",
            "regulatory_compliance",
            "tax_compliance",
            "intellectual_property",
            "data_protection",
            "other",
        ],
        f"got {ctx.get('matter_type')}",
    )
    assert check(
        "urgency valid",
        ctx.get("urgency") in ["critical", "high", "medium", "low", "unknown"],
        f"got {ctx.get('urgency')}",
    )
    assert check("facts_known is list", isinstance(ctx.get("facts_known"), list))
    assert check("facts_missing is list", isinstance(ctx.get("facts_missing"), list))
    assert check(
        "assistant has domain label",
        "Conformite du droit du travail" in (data.get("assistant_message", {}).get("content", ""))
        or "Conformit" in (data.get("assistant_message", {}).get("content", ""))
        or "labour" in (data.get("assistant_message", {}).get("content", "")).lower()
        or "travail" in (data.get("assistant_message", {}).get("content", "")).lower(),
    )

    print("\n  Assistant response preview:")
    assistant_content = data.get("assistant_message", {}).get("content", "")
    for line in assistant_content.split("\n")[:8]:
        print(f"    {line}")

    return {"case_id": case_id, "context": ctx}


def test_short_situation_rejected(client: TestClient, api_base_path: str, api_headers: dict):
    section("2. Schema validation - short situation rejected")

    resp = client.post(
        f"{api_base_path}/cases/from-conversation",
        json={"situation": "court"},
        headers=api_headers,
    )
    assert check("HTTP 422 for short situation", resp.status_code == 422, f"got {resp.status_code}")

    resp2 = client.post(
        f"{api_base_path}/cases/from-conversation",
        json={},
        headers=api_headers,
    )
    assert check("HTTP 422 for missing situation", resp2.status_code == 422, f"got {resp2.status_code}")


def test_follow_up_conversation(
    client: TestClient,
    api_base_path: str,
    api_headers: dict,
    created_case: dict,
):
    case_id = created_case["case_id"]
    ctx = created_case["context"]

    section(f"3. POST /cases/{case_id}/converse")
    resp = client.post(
        f"{api_base_path}/cases/{case_id}/converse",
        json={
            "content": "Ces 3 employes travaillent depuis 8 mois. Notre entreprise n'a pas encore de reglement interieur.",
        },
        headers=api_headers,
    )

    print(f"  {INFO} Status: {resp.status_code}")
    assert check("HTTP 201", resp.status_code == 201, f"got {resp.status_code}")

    d4 = resp.json()
    ctx4 = d4.get("context", {})
    print(f"  {INFO} facts_known ({len(ctx4.get('facts_known', []))}): {ctx4.get('facts_known')}")
    print(f"  {INFO} facts_missing ({len(ctx4.get('facts_missing', []))}): {ctx4.get('facts_missing')}")
    print(f"  {INFO} next_question: {ctx4.get('next_question')}")

    assert check("case_id matches", d4.get("case_id") == case_id, f"got {d4.get('case_id')}")
    assert check(
        "facts_known grew or same",
        len(ctx4.get("facts_known", [])) >= len(ctx.get("facts_known", [])),
        f"{len(ctx4.get('facts_known', []))} vs {len(ctx.get('facts_known', []))}",
    )
    assert check("context updated_at present", ctx4.get("updated_at") is not None)


def test_unknown_case_returns_404(
    client: TestClient,
    api_base_path: str,
    api_headers: dict,
    mock_case_backend: dict,
    monkeypatch,
):
    section("4. POST /cases/nonexistent-id/converse -> 404")

    from app.services import case_conversation_service

    async def raise_not_found(db, case_id, organization_id=None):
        raise HTTPException(status_code=404, detail="Case not found")

    monkeypatch.setattr(case_conversation_service.case_service, "get_case", raise_not_found)

    resp = client.post(
        f"{api_base_path}/cases/nonexistent-xyz-000/converse",
        json={"content": "Bonjour, question de test."},
        headers=api_headers,
    )
    assert check("HTTP 404 for unknown case", resp.status_code == 404, f"got {resp.status_code}")


def test_conversation_summary(
    client: TestClient,
    api_base_path: str,
    api_headers: dict,
    created_case: dict,
):
    case_id = created_case["case_id"]
    section(f"5. GET /cases/{case_id}/summary")

    resp = client.get(f"{api_base_path}/cases/{case_id}/summary", headers=api_headers)
    print(f"  {INFO} Status: {resp.status_code}")
    assert check("HTTP 200", resp.status_code == 200, f"got {resp.status_code}")

    s = resp.json()
    print(f"  {INFO} title: {s.get('title')}")
    print(f"  {INFO} status: {s.get('status')}")
    print(f"  {INFO} priority: {s.get('priority')}")
    print(f"  {INFO} message_count: {s.get('message_count')}")

    assert check("case_id present", s.get("case_id") == case_id)
    assert check("title non-empty", bool(s.get("title")))
    assert check("status present", bool(s.get("status")))
    assert check("priority present", bool(s.get("priority")))
    assert check("context present", bool(s.get("context")))
    assert check("message_count >= 4", s.get("message_count", 0) >= 4, f"got {s.get('message_count')}")

    resp2 = client.get(
        f"{api_base_path}/cases/nonexistent-xyz-000/summary",
        headers=api_headers,
    )
    assert check("HTTP 404 for unknown summary", resp2.status_code == 404, f"got {resp2.status_code}")


def test_unit_test_suite():
    section("6. Unit test suite")
    test_dir = Path(__file__).resolve().parent
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(test_dir / "test_case_conversation_service.py"),
            str(test_dir / "test_case_service.py"),
            "-q",
            "--tb=short",
        ],
        capture_output=True,
        text=True,
        cwd=os.getcwd(),
    )
    for line in result.stdout.splitlines()[-6:]:
        print(f"  {line}")
    assert check("All unit tests pass", result.returncode == 0, "see above")
