"""
# Daleel Locust Load Testing Suite
# Install:       pip install locust
# Run UI mode:   locust
# Run headless:  locust --headless -u 20 -r 2 --run-time 2m
"""

import os
import random
from io import BytesIO

from locust import HttpUser, between, task


API_KEY = os.getenv("DALEEL_API_KEY", "test-key")
BASE_HEADERS = {"X-API-Key": API_KEY}

LEGAL_QUESTIONS = [
    "Quels sont les droits d'un salarié licencié sans préavis en Tunisie ?",
    "ما هي الإجراءات القانونية لإنهاء عقد الشغل محدد المدة قبل الأجل؟",
    "Comment créer une SARL en Tunisie et quelles sont les obligations du gérant ?",
    "ما هي مسؤولية الشركاء في شركة ذات مسؤولية محدودة عند الديون الجبائية؟",
    "Quelles sont les obligations fiscales d'une PME en matière de TVA et de déclaration mensuelle ?",
    "كيف يمكن تسوية وضعية التصريح بالأجراء لدى CNSS وتفادي العقوبات؟",
    "Que vérifie l'inspection du travail lors d'un contrôle en entreprise ?",
    "ما هي الوثائق التي يجب توفيرها أثناء زيارة تفقد الشغل؟",
    "Quelles sont les obligations de protection des données personnelles en Tunisie (INPDP) ?",
    "Comment répondre à une demande de suppression de données personnelles d'un client ?",
]

CASE_SITUATIONS = [
    "Notre société emploie 25 salariés. Plusieurs heures supplémentaires ne sont pas payées et nous craignons un contrôle de l'inspection du travail.",
    "لدينا شركة ناشئة تجمع بيانات حرفاء عبر موقع إلكتروني ولم نقم بالتصريح لدى INPDP. ما هي المخاطر وخطة الامتثال؟",
    "Une SARL à Tunis a des retards de déclaration fiscale et souhaite régulariser sa situation sans pénalités majeures.",
]

CASE_FOLLOWUPS = [
    "Donne-moi un plan d'action priorisé sur 30 jours.",
    "ما هي الأولويات العاجلة خلال الأسبوع الأول؟",
    "Quels documents devons-nous préparer pour prouver la conformité ?",
]


def _minimal_pdf_bytes() -> bytes:
    # Minimal valid PDF content for upload testing.
    raw = (
        b"%PDF-1.1\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
        b"/Contents 4 0 R /Resources << >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 72 72 Td (Daleel test PDF) Tj ET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000062 00000 n \n0000000120 00000 n \n0000000225 00000 n \n"
        b"trailer\n<< /Root 1 0 R /Size 5 >>\nstartxref\n322\n%%EOF\n"
    )
    return raw


class ReadUser(HttpUser):
    weight = 5
    wait_time = between(2, 5)

    @task(2)
    def list_documents(self):
        self.client.get("/api/v1/documents", headers=BASE_HEADERS, name="GET /api/v1/documents")

    @task(2)
    def search(self):
        query = random.choice(LEGAL_QUESTIONS)
        payload = {"query": query, "top_k": 5}
        self.client.post(
            "/api/v1/search",
            json=payload,
            headers=BASE_HEADERS,
            name="POST /api/v1/search",
        )

    @task(1)
    def ask(self):
        question = random.choice(LEGAL_QUESTIONS)
        payload = {"question": question, "top_k": 5}
        self.client.post(
            "/api/v1/ask",
            json=payload,
            headers=BASE_HEADERS,
            name="POST /api/v1/ask",
        )


class UploadUser(HttpUser):
    weight = 1
    wait_time = between(10, 30)

    @task
    def upload_document(self):
        pdf_bytes = _minimal_pdf_bytes()
        files = {
            "file": (
                "locust_test.pdf",
                BytesIO(pdf_bytes),
                "application/pdf",
            )
        }
        self.client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=BASE_HEADERS,
            name="POST /api/v1/documents/upload",
        )


class ComplianceUser(HttpUser):
    weight = 2
    wait_time = between(5, 10)

    def on_start(self):
        self.case_id = None

    @task(2)
    def create_case_from_conversation(self):
        payload = {"conversation": random.choice(CASE_SITUATIONS)}
        with self.client.post(
            "/api/v1/cases/from-conversation",
            json=payload,
            headers=BASE_HEADERS,
            name="POST /api/v1/cases/from-conversation",
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.failure(f"Case creation failed: {response.status_code}")
                return
            data = response.json() if response.text else {}
            case_id = data.get("case_id")
            if not case_id:
                response.failure("Missing case_id in response")
                return
            self.case_id = case_id
            response.success()

    @task(1)
    def converse_on_case(self):
        if not self.case_id:
            self.create_case_from_conversation()
            return
        payload = {"message": random.choice(CASE_FOLLOWUPS)}
        self.client.post(
            f"/api/v1/cases/{self.case_id}/converse",
            json=payload,
            headers=BASE_HEADERS,
            name="POST /api/v1/cases/{case_id}/converse",
        )
