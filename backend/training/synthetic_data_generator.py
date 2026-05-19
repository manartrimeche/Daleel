"""
synthetic_data_generator.py

Génère des exemples synthétiques d'entraînement pour Track 1 (style) et Track 2 (reasoning)
en complément des données curated. Utilise des templates et des variations structurées
pour créer ~200 exemples de classification et ~50 exemples de style.

USAGE
-----
    python training/synthetic_data_generator.py --output-dir training/data/synthetic
"""
from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Track 2 — Classification examples
# ─────────────────────────────────────────────────────────────

DOMAINS = ["labor", "data_protection", "corporate", "credit_info", "investment", "other"]
CASE_TYPES = ["question", "complaint", "incident", "data_subject_request", "audit", "other"]
RISK_LEVELS = ["low", "medium", "high"]

QUESTION_TEMPLATES: dict[str, list[str]] = {
    "labor": [
        "Quelles sont les conditions de licenciement d'un salarié en Tunisie ?",
        "Un employé peut-il refuser un changement de poste ?",
        "Combien de jours de congé annuel sont prévus par le Code du travail ?",
        "Quelles sont les obligations de l'employeur en matière de formation ?",
        "Est-ce qu'un contrat à durée déterminée peut être renouvelé indéfiniment ?",
        "Un salarié peut-il cumuler deux emplois à temps plein ?",
        "Quel est le délai de préavis pour un CDI de plus de 5 ans ?",
        "Les heures supplémentaires sont-elles obligatoires ?",
        "Un stagiaire a-t-il droit aux congés payés ?",
        "Quelles sont les conditions de validité d'une clause de non-concurrence ?",
    ],
    "data_protection": [
        "Faut-il déclarer la collecte d'emails clients à l'INPDP ?",
        "Quelle est la durée maximale de conservation des données personnelles ?",
        "Un client peut-il demander la suppression de ses données ?",
        "Quelles sont les sanctions pour violation de la loi 63-2004 ?",
        "Le consentement doit-il être écrit pour la collecte de données ?",
        "Un sous-traitant hébergeant des données à l'étranger doit-il être agréé ?",
        "Quelles sont les obligations du DPO (Délégué à la Protection des Données) ?",
        "La vidéosurveillance dans les locaux de travail est-elle autorisée ?",
        "Faut-il informer les employés du traitement de leurs données biométriques ?",
        "Qu'est-ce qu'une violation de données personnelles ?",
    ],
    "corporate": [
        "Comment créer une SARL en Tunisie ?",
        "Quel est le capital minimum d'une SA ?",
        "Un associé peut-il céder ses parts sociales librement ?",
        "Quelles sont les obligations comptables d'une entreprise tunisienne ?",
        "Comment dissoudre une société ?",
        "Le commissaire aux comptes est-il obligatoire pour une SARL ?",
        "Quelles sont les conditions de transformation d'une SARL en SA ?",
        "Un gérant de SARL peut-il être rémunéré en parts sociales ?",
        "Quel est le délai de publication des comptes annuels au JORT ?",
        "Les assemblées générales peuvent-elles se tenir par visioconférence ?",
    ],
    "credit_info": [
        "Qu'est-ce que le fichier des incidents de paiement ?",
        "Comment contester une inscription au fichier des incidents ?",
        "Une banque peut-elle refuser un crédit sans justification ?",
        "Quelles sont les conditions d'octroi d'un crédit hypothécaire ?",
        "Le taux d'intérêt des crédits à la consommation est-il plafonné ?",
        "Un client peut-il demander une copie de son dossier de crédit ?",
        "Qu'est-ce que la Centrale des Risques ?",
        "Les établissements de crédit doivent-ils déclarer les opérations suspectes ?",
        "Quel est le délai de prescription des créances bancaires ?",
        "Un cautionnement solidaire peut-il être limité dans le temps ?",
    ],
    "investment": [
        "Quelles sont les conditions d'investissement étranger en Tunisie ?",
        "Un fonds d'investissement doit-il être agréé par le CMF ?",
        "Qu'est-ce qu'un OPCVM en droit tunisien ?",
        "Les actions d'une société cotée peuvent-elles être acquises par un étranger ?",
        "Quelles sont les incitations fiscales pour les investissements en zones de développement ?",
        "Un investisseur étranger peut-il détenir 100% du capital d'une entreprise ?",
        "Quel est le rôle de la BVMT dans la régulation des marchés ?",
        "La constitution d'une SICAV nécessite-t-elle une autorisation préalable ?",
        "Quelles sont les obligations de publication pour une société cotée ?",
        "Un pacte d'actionnaires est-il opposable aux tiers ?",
    ],
    "other": [
        "Quelles sont les conditions de validité d'un contrat de bail commercial ?",
        "Un fournisseur peut-il suspendre ses livraisons en cas de retard de paiement ?",
        "Quel est le délai de paiement légal pour les factures B2B ?",
        "La propriété intellectuelle d'un logiciel développé par un salarié appartient-elle à l'employeur ?",
        "Quelles sont les conditions d'exportation de biens vers l'Europe ?",
    ],
}

COMPLAINT_TEMPLATES: dict[str, list[str]] = {
    "labor": [
        "Mon employeur m'a licencié sans préavis après 8 ans de service. Je réclame des dommages.",
        "Je n'ai pas reçu mon salaire depuis 3 mois. Mon employeur refuse de me payer.",
        "J'ai été muté contre mon gré à un poste inférieur sans motif valable.",
        "Mon contrat de travail a été rompu pendant ma période d'essai mais j'ai travaillé 6 mois.",
        "L'employeur refuse de m'accorder mon congé annuel payé depuis 2 ans.",
        "J'ai subi du harcèlement moral de la part de mon supérieur hiérarchique.",
        "Mon employeur m'a forcé à signer une démission sans contrepartie.",
        "Je n'ai pas été indemnisé pour mon accident de travail survenu il y a 6 mois.",
        "Ma prime de rendement a été supprimée sans consultation du comité social.",
        "L'employeur a modifié mes horaires de travail sans mon accord écrit.",
    ],
    "data_protection": [
        "Ma banque a partagé mes données financières avec un partenaire commercial sans mon consentement.",
        "J'ai découvert que mon ancien employeur conserve encore mon dossier médical 3 ans après mon départ.",
        "Un site e-commerce a vendu mes coordonnées à des tiers. Je reçois des spams constants.",
        "Mon employeur a installé des caméras de surveillance dans les vestiaires sans nous informer.",
        "J'ai demandé la suppression de mon compte mais l'entreprise refuse de le faire.",
        "Mes données biométriques ont été collectées lors de l'embauche sans explication.",
        "Un appel téléphonique automatisé m'a contacté en utilisant mes données personnelles sans autorisation.",
        "Mon profil sur un réseau social professionnel a été copié par une agence de recrutement.",
        "L'entreprise a divulgué mon adresse personnelle à un fournisseur externe.",
        "Je n'ai jamais reçu d'information sur le traitement de mes données lors de mon inscription.",
    ],
    "corporate": [
        "Un associé a utilisé les fonds de la société à des fins personnelles sans autorisation de l'AGE.",
        "La majorité des associés a voté une distribution de dividendes fictive.",
        "Le gérant a signé un contrat engageant la société au-delà de ses pouvoirs statutaires.",
        "Un associé minoritaire a été exclu de l'assemblée générale sans justification.",
        "Les comptes annuels n'ont pas été approuvés dans les délais légaux depuis 2 ans.",
        "La société a été radiée du registre du commerce sans que les associés en soient informés.",
        "Un administrateur a voté un contrat dans lequel il a un intérêt personnel sans déclaration.",
        "Les statuts ont été modifiés unilatéralement par le gérant sans assemblée.",
        "La mise en liquidation a été décidée sans respecter les formalités de convocation.",
        "Un apport en nature a été surévalué lors de la constitution de la société.",
    ],
    "credit_info": [
        "Ma banque a inscrit mon nom au fichier des incidents de paiement pour un retard de 5 jours.",
        "J'ai été refusé pour un crédit immobilier alors que mon dossier est clean.",
        "La banque a augmenté mon taux d'intérêt sans m'en informer par écrit.",
        "Un prêt a été contracté à mon nom par fraude. Je demande la rectification du fichier.",
        "Mon cautionnement a été exécuté alors que la dette principale était prescrite.",
        "L'établissement de crédit a refusé de me communiquer les motifs de son refus de crédit.",
        "Mes données ont été inscrites au fichier des incidents par erreur. Je demande une correction.",
        "La banque a gelé mon compte sans justification ni notification préalable.",
        "Un prêt à la consommation a été vendu avec un taux usuraire de 25%.",
        "Le recouvrement forcé a été initié avant l'échéance du contrat de crédit.",
    ],
    "investment": [
        "Le fonds d'investissement a refusé de me rembourser ma quote-part sur demande.",
        "L'OPCVM a investi dans des actifs non conformes à son prospectus.",
        "Le gestionnaire de portefeuille a réalisé des opérations spéculatives non autorisées.",
        "Les informations financières fournies à l'AMF étaient fausses.",
        "Un investisseur étranger a été discriminé dans l'accès au capital d'une société tunisienne.",
        "La SICAV a suspendé les rachats sans justification réglementaire.",
        "Le commissaire aux comptes n'a pas signalé des irrégularités dans les comptes.",
        "Les actionnaires minoritaires n'ont pas été informés de l'OPA.",
        "Le dividende promis n'a pas été versé dans les délais statutaires.",
        "La valorisation des actifs du fonds a été manipulée artificiellement.",
    ],
    "other": [
        "Mon fournisseur a livré des marchandises défectueuses et refuse le remboursement.",
        "Le propriétaire a résilié mon bail commercial sans respecter le préavis légal.",
        "Un concurrent a copié ma marque déposée sur le marché tunisien.",
        "Le transporteur a perdu ma marchandise et refuse d'indemniser la perte.",
        "Le contrat de franchise a été résilié arbitrairement par le franchiseur.",
    ],
}

INCIDENT_TEMPLATES: dict[str, list[str]] = {
    "labor": [
        "Un accident de travail mortel s'est produit sur le chantier de construction à Sfax.",
        "L'inspection du travail a constaté des manquements graves aux normes d'hygiène.",
        "Un incendie a éclaté dans l'usine à cause d'un défaut d'entretien des extincteurs.",
        "Un salarié a été gravement blessé par une machine sans protection adéquate.",
        "Un cas d'intoxication alimentaire a été signalé dans la cantine d'entreprise.",
    ],
    "data_protection": [
        "Une fuite de données a exposé les informations de 10 000 clients sur internet.",
        "Un ransomware a chiffré les bases de données contenant des données sensibles.",
        "Un employé a envoyé par erreur un fichier confidentiel à un concurrent.",
        "L'INPDP a infligé une amende record à une entreprise pour non-conformité.",
        "Un audit a révélé l'absence totale de mesures de sécurité informatique.",
    ],
    "corporate": [
        "Le commissaire aux comptes a démissionné en raison d'irrégularités comptables.",
        "Un conflit entre associés a paralysé la gestion de la société depuis 6 mois.",
        "La société a fait l'objet d'une saisie conservatoire sur ses comptes bancaires.",
        "Un administrateur a été mis en examen pour abus de biens sociaux.",
        "La dissolution de la société a été prononcée par le tribunal de commerce.",
    ],
    "credit_info": [
        "Une fraude massive aux crédits à la consommation a été découverte dans une banque.",
        "Le système d'information de la Centrale des Risques a subi une panne majeure.",
        "Un blanchiment d'argent a été détecté dans les opérations de change.",
        "Un établissement de crédit a été placé sous administration provisoire.",
        "Une fuite de données clients bancaires a été signalée par la presse.",
    ],
    "investment": [
        "Le cours de l'action a chuté de 40% suite à une révélation d'informations privilégiées.",
        "Le fonds d'investissement a été victime d'une escroquerie pyramidale.",
        "Une OPA hostile a été lancée sur une société cotée sans autorisation du CMF.",
        "Le marché boursier a été suspendu en raison de manipulations de cours.",
        "Un gestionnaire d'actifs a été condamné pour délit d'initié.",
    ],
    "other": [
        "Un sinistre majeur a détruit l'entrepôt principal de l'entreprise.",
        "Un litige commercial international a bloqué les importations depuis 3 mois.",
        "Le système informatique de l'entreprise a été victime d'une cyberattaque.",
    ],
}


def _build_classification_examples() -> list[dict[str, Any]]:
    """Build ~180 synthetic classification examples."""
    examples: list[dict[str, Any]] = []
    id_counter = 1000

    for domain, templates in QUESTION_TEMPLATES.items():
        for text in templates:
            examples.append({
                "id": f"syn-class-{id_counter}",
                "task": "classify",
                "text": text,
                "language": "fr",
                "labels": {"domain": domain, "case_type": "question", "risk": "low"},
            })
            id_counter += 1

    for domain, templates in COMPLAINT_TEMPLATES.items():
        for text in templates:
            risk = random.choice(["medium", "high"]) if domain != "other" else "medium"
            examples.append({
                "id": f"syn-class-{id_counter}",
                "task": "classify",
                "text": text,
                "language": "fr",
                "labels": {"domain": domain, "case_type": "complaint", "risk": risk},
            })
            id_counter += 1

    for domain, templates in INCIDENT_TEMPLATES.items():
        for text in templates:
            examples.append({
                "id": f"syn-class-{id_counter}",
                "task": "classify",
                "text": text,
                "language": "fr",
                "labels": {"domain": domain, "case_type": "incident", "risk": "high"},
            })
            id_counter += 1

    # Add some audit and data_subject_request examples
    audit_examples = [
        ("L'audit interne a révélé des écarts dans l'application de la politique RH.", "labor", "medium"),
        ("L'audit INPDP a sanctionné l'absence de registre des traitements.", "data_protection", "high"),
        ("Le commissaire aux comptes a émis une réserve sur les comptes annuels.", "corporate", "high"),
        ("L'inspection bancaire a relevé des non-conformités dans les pratiques de crédit.", "credit_info", "high"),
        ("L'audit du CMF a constaté des manquements dans la gestion du fonds.", "investment", "high"),
    ]
    for text, domain, risk in audit_examples:
        examples.append({
            "id": f"syn-class-{id_counter}",
            "task": "classify",
            "text": text,
            "language": "fr",
            "labels": {"domain": domain, "case_type": "audit", "risk": risk},
        })
        id_counter += 1

    dsr_examples = [
        ("Un client demande l'accès à ses données collectées par notre site web.", "data_protection", "low"),
        ("Un ancien salarié réclame la destruction de son dossier personnel.", "data_protection", "medium"),
        ("Un patient demande la rectification de ses informations médicales dans notre base.", "data_protection", "medium"),
    ]
    for text, domain, risk in dsr_examples:
        examples.append({
            "id": f"syn-class-{id_counter}",
            "task": "classify",
            "text": text,
            "language": "fr",
            "labels": {"domain": domain, "case_type": "data_subject_request", "risk": risk},
        })
        id_counter += 1

    # Add some Arabic examples
    ar_examples = [
        ("ما هي حقوق العمال في حالة إفلاس الشركة؟", "labor", "question", "medium"),
        ("تم فصلي من العمل دون سبب مشروع وأطالب بتعويض", "labor", "complaint", "high"),
        ("هل يجب الحصول على موافقة العميل قبل جمع بياناته الشخصية؟", "data_protection", "question", "low"),
        ("شركتي ترغب في معرفة إجراءات تأسيس فرع في أوروبا", "corporate", "question", "low"),
        ("بنكي رفض منحي قرضا دون توضيح الأسباب", "credit_info", "complaint", "medium"),
    ]
    for text, domain, ctype, risk in ar_examples:
        examples.append({
            "id": f"syn-class-{id_counter}",
            "task": "classify",
            "text": text,
            "language": "ar",
            "labels": {"domain": domain, "case_type": ctype, "risk": risk},
        })
        id_counter += 1

    random.shuffle(examples)
    return examples


def _build_style_examples() -> list[dict[str, Any]]:
    """Build ~30 synthetic style examples (smaller set, high quality)."""
    # We'll generate these by creating simple input/output pairs using templates
    # For brevity, we'll create shorter structured outputs focusing on key sections
    examples = []
    id_counter = 2000

    topics = [
        {
            "question": "Comment calculer l'indemnité de licenciement en Tunisie ?",
            "domain": "labor",
            "facts": {"parties": ["employeur", "salarié"], "case_type": "question", "dates": [], "amounts": []},
            "risk": "low",
            "draft": "L'indemnité de licenciement est calculée selon l'ancienneté du salarié.",
        },
        {
            "question": "Mon employeur refuse de me payer mes heures supplémentaires.",
            "domain": "labor",
            "facts": {"parties": ["salarié", "employeur"], "case_type": "complaint", "dates": [], "amounts": []},
            "risk": "medium",
            "draft": "Le non-paiement des heures supplémentaires constitue une violation du Code du travail.",
        },
        {
            "question": "Notre société collecte les CIN de nos clients. Sommes-nous en conformité ?",
            "domain": "data_protection",
            "facts": {"parties": ["société", "clients"], "case_type": "question", "dates": [], "amounts": []},
            "risk": "medium",
            "draft": "La collecte de données d'identité nécessite une déclaration auprès de l'INPDP.",
        },
        {
            "question": "Je veux créer une startup en Tunisie. Quelle forme juridique choisir ?",
            "domain": "corporate",
            "facts": {"parties": ["entrepreneur"], "case_type": "question", "dates": [], "amounts": []},
            "risk": "low",
            "draft": "Le choix de la forme juridique dépend du nombre d'associés et du capital.",
        },
        {
            "question": "La banque a augmenté mon taux d'intérêt sans me prévenir.",
            "domain": "credit_info",
            "facts": {"parties": ["client", "banque"], "case_type": "complaint", "dates": [], "amounts": []},
            "risk": "high",
            "draft": "Toute modification du taux d'intérêt doit être notifiée par écrit au client.",
        },
    ]

    for topic in topics:
        output = (
            f"## Ce que j'ai compris\n"
            f"Votre question porte sur {topic['domain']} en droit tunisien.\n\n"
            f"## Informations manquantes\n"
            f"- Détails complémentaires sur la situation spécifique.\n"
            f"- Documents et preuves disponibles.\n\n"
            f"## Contexte légal / articles pertinents\n"
            f"- Articles pertinents du Code applicable.\n\n"
            f"## Analyse / risques de non-conformité\n"
            f"- Risque identifié : {topic['risk']}.\n\n"
            f"## Actions recommandées\n"
            f"1. Consulter un avocat spécialisé.\n"
            f"2. Rassembler les documents probants.\n\n"
            f"## Preuves / documents à rassembler\n"
            f"- Contrats, correspondances, preuves matérielles.\n\n"
            f"## Nécessité d'une revue humaine\n"
            f"Oui — recommandée pour validation finale."
        )

        examples.append({
            "id": f"syn-style-{id_counter}",
            "input": {
                "language": "fr",
                "user_question": topic["question"],
                "extracted_facts": topic["facts"],
                "legal_context": [{"article_ref": "Code applicable", "text": "Article relatif à la matière."}],
                "findings": [{"title": "Analyse préliminaire", "severity": topic["risk"], "gap": "Analyse à compléter."}],
                "actions": [{"title": "Consulter un spécialiste", "priority": "high"}],
                "draft_answer": topic["draft"],
            },
            "output": output,
        })
        id_counter += 1

    return examples


def generate(output_dir: Path, train_ratio: float = 0.85) -> tuple[Path, Path, Path, Path]:
    """Generate synthetic datasets and split into train/eval."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track 2
    classify_examples = _build_classification_examples()
    logger.info("Generated %d synthetic classification examples", len(classify_examples))

    split_idx = int(len(classify_examples) * train_ratio)
    classify_train = classify_examples[:split_idx]
    classify_eval = classify_examples[split_idx:]

    reasoning_train_file = output_dir / "reasoning_synthetic_train.jsonl"
    reasoning_eval_file = output_dir / "reasoning_synthetic_eval.jsonl"

    with reasoning_train_file.open("w", encoding="utf-8") as f:
        for ex in classify_train:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    with reasoning_eval_file.open("w", encoding="utf-8") as f:
        for ex in classify_eval:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    logger.info("Wrote %d train / %d eval → %s", len(classify_train), len(classify_eval), reasoning_train_file.parent)

    # Track 1
    style_examples = _build_style_examples()
    logger.info("Generated %d synthetic style examples", len(style_examples))

    split_idx_s = max(1, int(len(style_examples) * train_ratio))
    style_train = style_examples[:split_idx_s]
    style_eval = style_examples[split_idx_s:]

    style_train_file = output_dir / "style_synthetic_train.jsonl"
    style_eval_file = output_dir / "style_synthetic_eval.jsonl"

    with style_train_file.open("w", encoding="utf-8") as f:
        for ex in style_train:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    with style_eval_file.open("w", encoding="utf-8") as f:
        for ex in style_eval:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    logger.info("Wrote %d train / %d eval → %s", len(style_train), len(style_eval), style_train_file.parent)

    return reasoning_train_file, reasoning_eval_file, style_train_file, style_eval_file


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, default=Path("training/data/synthetic"))
    p.add_argument("--train-ratio", type=float, default=0.85)
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    generate(args.output_dir, args.train_ratio)


if __name__ == "__main__":
    main()
