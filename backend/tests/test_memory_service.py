"""Tests pour memory_service — faits utilisateur + résumé roulant."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import memory_service


def _make_db(user_memory_doc=None, summary_doc=None):
    """Construit un faux ``db`` Motor minimaliste."""
    user_memory = MagicMock()
    user_memory.find_one = AsyncMock(return_value=user_memory_doc)
    user_memory.update_one = AsyncMock()
    user_memory.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))

    conv_summaries = MagicMock()
    conv_summaries.find_one = AsyncMock(return_value=summary_doc)
    conv_summaries.update_one = AsyncMock()

    db = MagicMock()
    db.__getitem__.side_effect = lambda name: {
        "user_memory": user_memory,
        "conversation_summaries": conv_summaries,
    }[name]
    return db, user_memory, conv_summaries


# ──────────────────────── user_memory ────────────────────────


@pytest.mark.asyncio
async def test_get_user_memory_returns_none_for_blank_user():
    db, _, _ = _make_db()
    assert await memory_service.get_user_memory(db, "") is None
    assert await memory_service.get_user_memory(db, None) is None


@pytest.mark.asyncio
async def test_upsert_user_facts_merges_and_dedupes():
    existing = {"facts": ["Société = ACME SA", "Juridiction = Tunisie"]}
    db, user_memory, _ = _make_db(user_memory_doc=existing)

    doc = await memory_service.upsert_user_facts(
        db,
        user_id="u1",
        facts=["société = acme sa", "Préfère le français"],  # premier = doublon (casse)
        organization_id="org1",
    )

    # Doublons éliminés (cmp insensible à la casse), nouveaux faits en tête.
    facts = doc["facts"]
    assert facts[0] == "société = acme sa"  # version reçue conserve sa casse
    assert "Préfère le français" in facts
    assert "Juridiction = Tunisie" in facts
    # "Société = ACME SA" prior doublonne avec le nouveau → un seul exemplaire.
    assert len(facts) == 3
    user_memory.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_user_facts_replace_mode_overwrites():
    existing = {"facts": ["ancien fait"]}
    db, _, _ = _make_db(user_memory_doc=existing)

    doc = await memory_service.upsert_user_facts(
        db, user_id="u1", facts=["nouveau"], replace=True
    )
    assert doc["facts"] == ["nouveau"]


@pytest.mark.asyncio
async def test_upsert_user_facts_drops_overlong_and_empty():
    db, _, _ = _make_db(user_memory_doc=None)
    too_long = "x" * (memory_service.MAX_FACT_LENGTH + 1)
    doc = await memory_service.upsert_user_facts(
        db, user_id="u1", facts=["", "   ", too_long, "ok"], replace=True
    )
    assert doc["facts"] == ["ok"]


@pytest.mark.asyncio
async def test_upsert_user_facts_caps_to_max():
    db, _, _ = _make_db(user_memory_doc=None)
    many = [f"fait n°{i}" for i in range(memory_service.MAX_USER_FACTS + 5)]
    doc = await memory_service.upsert_user_facts(
        db, user_id="u1", facts=many, replace=True
    )
    assert len(doc["facts"]) == memory_service.MAX_USER_FACTS


@pytest.mark.asyncio
async def test_delete_user_memory_returns_bool():
    db, user_memory, _ = _make_db()
    assert await memory_service.delete_user_memory(db, "u1") is True
    user_memory.delete_one.assert_awaited_once()


# ──────────────────────── conversation summary ────────────────────────


@pytest.mark.asyncio
async def test_maybe_update_summary_skips_when_history_short():
    db, _, conv = _make_db()
    history = [{"role": "user", "content": "q?"}] * 5
    assert await memory_service.maybe_update_summary(db, "c1", history) is None
    conv.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_update_summary_skips_without_conversation_id():
    db, _, conv = _make_db()
    history = [{"role": "user", "content": "x"}] * 50
    assert await memory_service.maybe_update_summary(db, None, history) is None
    conv.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_update_summary_writes_when_threshold_crossed():
    db, _, conv = _make_db(summary_doc=None)
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
        for i in range(memory_service.SUMMARY_TRIGGER_MESSAGES + 5)
    ]

    with patch.object(
        memory_service,
        "_generate_summary",
        new=AsyncMock(return_value="- point 1\n- point 2"),
    ) as gen:
        doc = await memory_service.maybe_update_summary(
            db, "c1", history, detected_lang="fr", user_id="u1"
        )

    gen.assert_awaited_once()
    assert doc is not None
    assert doc["summary"] == "- point 1\n- point 2"
    assert doc["messages_indexed"] == len(history) - memory_service.SUMMARY_KEEP_RECENT
    conv.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_maybe_update_summary_returns_existing_when_no_new_messages():
    existing = {
        "summary": "ancien",
        "messages_indexed": 100,
        "conversation_id": "c1",
    }
    db, _, conv = _make_db(summary_doc=existing)
    # 100 messages déjà indexés, on en a 102 → trop peu de nouveaux.
    history = [{"role": "user", "content": "x"}] * 102

    with patch.object(memory_service, "_generate_summary", new=AsyncMock()) as gen:
        doc = await memory_service.maybe_update_summary(db, "c1", history)

    gen.assert_not_called()
    conv.update_one.assert_not_called()
    assert doc == existing


# ──────────────────────── prompt helpers ────────────────────────


def test_build_memory_block_renders_facts_and_summary_fr():
    out = memory_service.build_memory_block(
        user_memory={"facts": ["Société = ACME", "Juridiction = TN"]},
        summary={"summary": "- résumé"},
        detected_lang="fr",
    )
    assert "Faits utilisateur persistants" in out
    assert "Société = ACME" in out
    assert "Résumé de la conversation antérieure" in out
    assert "- résumé" in out


def test_build_memory_block_empty_when_nothing():
    assert memory_service.build_memory_block(None, None, "fr") == ""
    assert memory_service.build_memory_block({"facts": []}, {"summary": ""}, "fr") == ""


def test_build_memory_block_falls_back_to_en_for_unknown_lang():
    out = memory_service.build_memory_block(
        user_memory={"facts": ["x"]}, summary=None, detected_lang="zz"
    )
    assert "Persistent user facts" in out


def test_trim_history_after_summary_drops_indexed_prefix():
    history = [{"role": "user", "content": str(i)} for i in range(10)]
    summary = {"messages_indexed": 6}
    trimmed = memory_service.trim_history_after_summary(history, summary)
    assert trimmed == history[6:]


def test_trim_history_after_summary_noop_without_summary():
    history = [{"role": "user", "content": "a"}]
    assert memory_service.trim_history_after_summary(history, None) == history
    assert memory_service.trim_history_after_summary(history, {"messages_indexed": 0}) == history


def test_trim_history_after_summary_noop_when_indexed_exceeds_history():
    history = [{"role": "user", "content": "a"}]
    assert memory_service.trim_history_after_summary(history, {"messages_indexed": 99}) == history
