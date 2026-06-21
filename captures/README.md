# Captures d'écran à insérer

Chaque fichier PNG manquant ci-dessous doit être remplacé par une capture
d'écran réelle de l'application Daleel. Les noms correspondent aux figures
du rapport `Rapport_Daleel_v2.md`.

| Fichier | Figure | Description |
|---|---|---|
| `fig_3_1_chat_reponse.png` | 4.1 | Réponse RAG dans le chatbot avec sources cliquables et badge garde-qualité |
| `fig_3_2_agent_tool_log.png` | 4.2 | Journal de raisonnement agent ReAct (séquence outils invoqués) |
| `fig_3_3_derja.png` | 4.3 | Détection et normalisation d'une requête en derja tunisien |
| `fig_4_1_chatbot.png` | 5.1 | Interface du chatbot conversationnel multilingue |
| `fig_4_2_admin_documents.png` | 5.2 | Panneau d'administration : gestion documentaire |
| `fig_4_3_dashboard.png` | 5.3 | Tableau de bord BI de la posture de conformité |
| `fig_5_4_finetuning_resultats.png` | 5.4 | Histogramme comparatif métriques fine-tuning (baseline vs Daleel) |

## Comment générer les captures

1. Lancer le backend : `cd backend && uvicorn app.main:app --reload`
2. Lancer le frontend : `cd frontend && npm run dev`
3. Se connecter avec un compte test
4. Capturer chaque écran (Windows : Win+Shift+S)
5. Sauvegarder dans ce dossier avec le nom exact ci-dessus
