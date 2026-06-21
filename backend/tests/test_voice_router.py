from unittest.mock import AsyncMock, patch


def test_voice_ask_rejects_unclear_transcription(test_client):
    unclear_transcription = {
        "text": "Sous-titres realises par la communaute",
        "language": "fr",
        "language_probability": 0.2,
        "is_confident": False,
        "confidence_reasons": ["low_language_probability", "likely_silence"],
    }

    with patch(
        "app.api.voice_router.transcribe_audio",
        new=AsyncMock(return_value=unclear_transcription),
    ), patch("app.api.voice_router.llm_service.ask_agentic", new_callable=AsyncMock) as mock_ask:
        response = test_client.post(
            "/api/v1/voice/ask",
            files={"audio": ("sample.wav", b"not-really-audio", "audio/wav")},
        )

    assert response.status_code == 422
    assert response.json()["detail"]["message"] == "Speech was too unclear to answer reliably"
    mock_ask.assert_not_awaited()


def test_voice_ask_passes_quality_guard_for_clear_transcription(test_client):
    clear_transcription = {
        "text": "Quelles sont les obligations du gerant ?",
        "language": "fr",
        "language_probability": 0.95,
        "is_confident": True,
        "avg_logprob": -0.2,
        "no_speech_probability": 0.03,
        "compression_ratio": 1.1,
    }

    with patch(
        "app.api.voice_router.transcribe_audio",
        new=AsyncMock(return_value=clear_transcription),
    ), patch(
        "app.api.voice_router.llm_service.ask_agentic",
        new=AsyncMock(return_value={"answer": "Reponse fondee.", "sources": []}),
    ) as mock_ask, patch(
        "app.api.voice_router.synthesize_speech",
        new=AsyncMock(return_value=b"audio"),
    ):
        response = test_client.post(
            "/api/v1/voice/ask",
            files={"audio": ("sample.wav", b"clear-audio", "audio/wav")},
        )

    assert response.status_code == 200
    assert response.json()["transcription_confidence"]["is_confident"] is True
    assert mock_ask.await_args.kwargs["use_quality_guard"] is True
