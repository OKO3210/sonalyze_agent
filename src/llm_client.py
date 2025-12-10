"""
Module LLM Client - Interprétation IA via Groq API
Génère les textes d'interprétation et recommandations pour le rapport DPS.

Utilise Llama 3.1 70B via Groq (rapide et gratuit).
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"  # Rapide et performant


def get_groq_client():
    """
    Initialise le client Groq.
    Retourne None si la clé API n'est pas configurée.
    """
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY non configurée dans .env")
        return None

    try:
        from groq import Groq

        return Groq(api_key=GROQ_API_KEY)
    except ImportError:
        print("⚠️ Package 'groq' non installé. Run: pip install groq")
        return None


def call_groq(
    prompt: str, system_prompt: str = None, temperature: float = 0.3
) -> Optional[str]:
    """
    Appelle l'API Groq avec un prompt.

    Args:
        prompt: Le prompt utilisateur
        system_prompt: Le prompt système (rôle)
        temperature: Créativité (0.0 = déterministe, 1.0 = créatif)

    Returns:
        Réponse du LLM ou None si erreur
    """
    client = get_groq_client()
    if not client:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Erreur Groq API: {e}")
        return None


# =============================================================================
# PROMPTS SYSTÈME
# =============================================================================

SYSTEM_ACOUSTICIAN = """Tu es un expert acousticien pédagogue spécialisé dans le diagnostic sonore des logements.
Tu expliques les résultats de manière claire et accessible pour des particuliers non-experts.
Tu es rassurant mais honnête. Tu donnes des conseils pratiques et actionnables.
Tu réponds TOUJOURS en français.
Tu évites le jargon technique, ou tu l'expliques simplement quand c'est nécessaire."""


# =============================================================================
# FONCTIONS DE GÉNÉRATION DE CONTENU
# =============================================================================


def generate_grade_interpretation(
    analysis: Dict[str, Any], logement_info: Dict[str, Any]
) -> str:
    """
    Génère l'interprétation de la note DPS (A-G).

    Args:
        analysis: Résultat de aggregator.generate_full_analysis()
        logement_info: Infos du logement (type, étage, pièce, etc.)

    Returns:
        Texte d'interprétation (2-3 paragraphes)
    """
    global_stats = analysis.get("global", {})
    day_night = analysis.get("day_night", {})

    prompt = f"""Voici les résultats d'un diagnostic de performance sonore (DPS) :

LOGEMENT :
- Type : {logement_info.get('type', 'Appartement')}
- Étage : {logement_info.get('etage', 'Non précisé')}
- Pièce analysée : {logement_info.get('piece', 'Salon')}
- Ville : {logement_info.get('ville', 'Non précisée')}

RÉSULTATS :
- Note globale : {global_stats.get('note_globale', 'D')}
- Niveau sonore moyen : {global_stats.get('db_mean', 45):.1f} dB
- Niveau minimum : {global_stats.get('db_min', 30):.1f} dB
- Niveau maximum : {global_stats.get('db_max', 70):.1f} dB
- Durée d'enregistrement : {global_stats.get('duration_hours', 24):.1f} heures

JOUR vs NUIT :
- Moyenne jour (7h-22h) : {day_night.get('jour', {}).get('mean', 50):.1f} dB
- Moyenne nuit (22h-7h) : {day_night.get('nuit', {}).get('mean', 40):.1f} dB

ÉCHELLE DPS :
- A (≤20 dB) : Exceptionnel - Silence quasi-total
- B (≤30 dB) : Très bon - Très calme
- C (≤45 dB) : Bon - Calme
- D (≤60 dB) : Moyen - Modéré
- E (≤80 dB) : Insuffisant - Bruyant
- F (≤100 dB) : Très insuffisant - Très bruyant
- G (>100 dB) : Critique - Dangereux

TÂCHE :
Rédige une interprétation de cette note en 2-3 paragraphes courts.
- Explique ce que signifie concrètement cette note pour l'habitant
- Compare aux seuils recommandés pour ce type de pièce
- Mentionne la différence jour/nuit si significative
- Sois rassurant mais honnête

Format : Texte simple, pas de bullet points, pas de titres."""

    result = call_groq(prompt, SYSTEM_ACOUSTICIAN)

    # Fallback si API échoue
    if not result:
        note = global_stats.get("note_globale", "D")
        db = global_stats.get("db_mean", 45)
        return f"""Votre logement obtient la note {note} avec un niveau sonore moyen de {db:.0f} dB. 
Cette note correspond à un confort acoustique {"correct" if note in ['A','B','C'] else "moyen" if note == 'D' else "insuffisant"}.
Pour plus de détails sur les sources de bruit et les recommandations, consultez les sections suivantes du rapport."""

    return result


def generate_sounds_analysis(analysis: Dict[str, Any]) -> str:
    """
    Génère l'analyse des sources sonores détectées.

    Args:
        analysis: Résultat de aggregator.generate_full_analysis()

    Returns:
        Texte d'analyse des bruits (2-3 paragraphes)
    """
    top_sounds = analysis.get("sounds", {}).get("top_20", [])[:10]
    families = analysis.get("sounds", {}).get("families_pct", {})
    classified = analysis.get("sounds", {}).get("classification", {})

    # Préparer les données pour le prompt
    sounds_text = "\n".join(
        [
            f"- {s['label']}: {s['percentage']:.1f}% du temps, {s['avg_score']:.3f} confiance, famille: {s['family']}"
            for s in top_sounds[:8]
        ]
    )

    families_text = "\n".join(
        [
            f"- {family}: {pct:.1f}%"
            for family, pct in sorted(
                families.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]
    )

    normal = classified.get("normaux", [])[:5]
    problematic = classified.get("problematiques_frequents", [])[:5]

    prompt = f"""Voici les sources sonores détectées lors d'un diagnostic acoustique sur 24h :

TOP SONS DÉTECTÉS :
{sounds_text}

RÉPARTITION PAR FAMILLE :
{families_text}

SONS NORMAUX IDENTIFIÉS : {', '.join(normal) if normal else 'Aucun'}
SONS PROBLÉMATIQUES FRÉQUENTS : {', '.join(problematic) if problematic else 'Aucun'}

TÂCHE :
Rédige une analyse des sources de bruit en 2-3 paragraphes.
- Identifie les sources principales de nuisance
- Distingue les bruits normaux (vie quotidienne) des bruits problématiques
- Mentionne si certains bruits sont ponctuels vs constants
- Donne des pistes sur l'origine probable (extérieur, voisinage, intérieur)

Format : Texte simple, pas de bullet points, pas de titres."""

    result = call_groq(prompt, SYSTEM_ACOUSTICIAN)

    if not result:
        main_sound = top_sounds[0]["label"] if top_sounds else "circulation"
        return f"""L'analyse sur 24h révèle que la source sonore principale est "{main_sound}".
Les bruits détectés proviennent majoritairement de l'environnement extérieur.
Consultez les graphiques ci-dessous pour une vue détaillée par heure et par type de bruit."""

    return result


def generate_recommendations(
    analysis: Dict[str, Any], logement_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Génère des recommandations personnalisées par élément du logement.

    Args:
        analysis: Résultat de aggregator.generate_full_analysis()
        logement_info: Infos du logement

    Returns:
        Dict avec recommandations structurées par catégorie
    """
    global_stats = analysis.get("global", {})
    families = analysis.get("sounds", {}).get("families_pct", {})
    classified = analysis.get("sounds", {}).get("classification", {})

    # Identifier les problèmes principaux
    note = global_stats.get("note_globale", "D")
    problematic = classified.get("problematiques_frequents", [])

    # Préparer contexte
    main_issues = []
    if families.get("circulation", 0) > 30:
        main_issues.append("bruit de circulation important")
    if families.get("voisinage", 0) > 20:
        main_issues.append("bruits de voisinage")
    if families.get("travaux", 0) > 10:
        main_issues.append("bruits de travaux")

    prompt = f"""Contexte du diagnostic acoustique :

LOGEMENT :
- Type : {logement_info.get('type', 'Appartement')}
- Étage : {logement_info.get('etage', 'Non précisé')}
- Pièce : {logement_info.get('piece', 'Salon')}

RÉSULTATS :
- Note globale : {note}
- Niveau moyen : {global_stats.get('db_mean', 45):.0f} dB
- Problèmes identifiés : {', '.join(main_issues) if main_issues else 'Modérés'}

TÂCHE :
Génère des recommandations personnalisées au format JSON avec cette structure exacte :
{{
  "fenetre": {{
    "priorite": "haute/moyenne/basse",
    "probleme": "description courte du problème",
    "solutions": [
      {{"nom": "nom solution", "cout": "fourchette €", "impact": "réduction dB estimée", "difficulte": "facile/moyen/difficile"}}
    ]
  }},
  "mur": {{ ... }},
  "porte": {{ ... }},
  "plafond": {{ ... }},
  "sol": {{ ... }},
  "aeration": {{ ... }}
}}

Adapte les recommandations selon :
- Si circulation > 30% → priorité fenêtres
- Si voisinage vertical > 20% → priorité plafond/sol
- Si note A-C → recommandations légères (entretien)
- Si note D-E → recommandations moyennes
- Si note F-G → recommandations lourdes (travaux)

Réponds UNIQUEMENT avec le JSON, sans texte avant/après."""

    result = call_groq(prompt, SYSTEM_ACOUSTICIAN, temperature=0.2)

    if result:
        try:
            # Nettoyer le JSON (enlever markdown si présent)
            json_str = result.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            json_str = json_str.strip()

            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # Fallback avec recommandations par défaut
    return get_default_recommendations(note, families)


def get_default_recommendations(
    note: str, families: Dict[str, float]
) -> Dict[str, Any]:
    """Recommandations par défaut si l'API échoue."""

    is_circulation = families.get("circulation", 0) > 30
    is_voisinage = families.get("voisinage", 0) > 20
    is_severe = note in ["E", "F", "G"]

    return {
        "fenetre": {
            "priorite": "haute" if is_circulation else "moyenne",
            "probleme": (
                "Transmission du bruit extérieur"
                if is_circulation
                else "Étanchéité à vérifier"
            ),
            "solutions": [
                {
                    "nom": "Joints d'étanchéité",
                    "cout": "50-100€",
                    "impact": "-5 à -10 dB",
                    "difficulte": "facile",
                },
                {
                    "nom": "Rideaux phoniques",
                    "cout": "100-200€",
                    "impact": "-3 à -5 dB",
                    "difficulte": "facile",
                },
                (
                    {
                        "nom": "Double/triple vitrage",
                        "cout": "3000-6000€",
                        "impact": "-15 à -25 dB",
                        "difficulte": "difficile",
                    }
                    if is_severe
                    else None
                ),
            ],
        },
        "mur": {
            "priorite": "moyenne" if is_voisinage else "basse",
            "probleme": (
                "Transmission latérale" if is_voisinage else "Isolation standard"
            ),
            "solutions": [
                {
                    "nom": "Panneaux acoustiques décoratifs",
                    "cout": "100-300€",
                    "impact": "-3 à -5 dB",
                    "difficulte": "facile",
                },
                (
                    {
                        "nom": "Doublage isolant",
                        "cout": "2000-5000€",
                        "impact": "-10 à -15 dB",
                        "difficulte": "difficile",
                    }
                    if is_severe
                    else None
                ),
            ],
        },
        "plafond": {
            "priorite": "haute" if is_voisinage else "basse",
            "probleme": "Bruits d'impact du dessus" if is_voisinage else "RAS",
            "solutions": (
                [
                    {
                        "nom": "Faux plafond acoustique",
                        "cout": "3000-8000€",
                        "impact": "-15 à -25 dB",
                        "difficulte": "difficile",
                    }
                ]
                if is_voisinage
                else []
            ),
        },
        "sol": {
            "priorite": "basse",
            "probleme": "Transmission vers le dessous",
            "solutions": [
                {
                    "nom": "Tapis épais",
                    "cout": "100-300€",
                    "impact": "-3 à -5 dB",
                    "difficulte": "facile",
                },
                {
                    "nom": "Sous-couche acoustique",
                    "cout": "500-1500€",
                    "impact": "-10 à -15 dB",
                    "difficulte": "moyen",
                },
            ],
        },
        "porte": {
            "priorite": "moyenne",
            "probleme": "Passage du son",
            "solutions": [
                {
                    "nom": "Bas de porte",
                    "cout": "20-50€",
                    "impact": "-3 à -5 dB",
                    "difficulte": "facile",
                },
                {
                    "nom": "Porte acoustique",
                    "cout": "500-1500€",
                    "impact": "-10 à -20 dB",
                    "difficulte": "moyen",
                },
            ],
        },
        "aeration": {
            "priorite": "basse",
            "probleme": "Entrée d'air = entrée de bruit",
            "solutions": [
                {
                    "nom": "Entrées d'air acoustiques",
                    "cout": "50-150€",
                    "impact": "-5 à -10 dB",
                    "difficulte": "moyen",
                }
            ],
        },
    }


def generate_summary_email(
    analysis: Dict[str, Any], logement_info: Dict[str, Any]
) -> str:
    """
    Génère un email de synthèse pour le client.

    Args:
        analysis: Résultat de aggregator.generate_full_analysis()
        logement_info: Infos du logement

    Returns:
        Texte de l'email
    """
    global_stats = analysis.get("global", {})
    note = global_stats.get("note_globale", "D")
    db = global_stats.get("db_mean", 45)

    prompt = f"""Rédige un email de synthèse pour un client ayant reçu son diagnostic acoustique.

INFOS :
- Nom : {logement_info.get('nom', 'Client')}
- Adresse : {logement_info.get('adresse', 'Non précisée')}
- Note obtenue : {note}
- Niveau moyen : {db:.0f} dB

L'email doit :
- Remercier pour la confiance
- Résumer la note en 1 phrase
- Donner 2-3 conseils prioritaires
- Proposer un accompagnement (optionnel)
- Être chaleureux et professionnel

Format : Email prêt à envoyer (avec Objet:, puis le corps)."""

    result = call_groq(prompt, SYSTEM_ACOUSTICIAN)

    if not result:
        return f"""Objet : Votre diagnostic de performance sonore - Note {note}

Bonjour,

Merci d'avoir fait confiance à Sonalyze pour votre diagnostic acoustique.

Votre logement obtient la note {note} avec un niveau sonore moyen de {db:.0f} dB.

Nous vous invitons à consulter le rapport complet ci-joint pour découvrir nos recommandations personnalisées.

N'hésitez pas à nous contacter pour toute question.

Cordialement,
L'équipe Sonalyze"""

    return result


def generate_all_interpretations(
    analysis: Dict[str, Any], logement_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Génère tous les textes d'interprétation en un seul appel.

    Args:
        analysis: Résultat de aggregator.generate_full_analysis()
        logement_info: Infos du logement

    Returns:
        Dict avec tous les textes générés
    """
    print("🧠 Génération des interprétations IA...")

    print("  → Interprétation de la note...")
    grade_interpretation = generate_grade_interpretation(analysis, logement_info)

    print("  → Analyse des sources sonores...")
    sounds_analysis = generate_sounds_analysis(analysis)

    print("  → Recommandations personnalisées...")
    recommendations = generate_recommendations(analysis, logement_info)

    print("  → Email de synthèse...")
    summary_email = generate_summary_email(analysis, logement_info)

    print("✅ Interprétations générées")

    return {
        "grade_interpretation": grade_interpretation,
        "sounds_analysis": sounds_analysis,
        "recommendations": recommendations,
        "summary_email": summary_email,
    }


# =============================================================================
# TEST DU MODULE
# =============================================================================

if __name__ == "__main__":
    """Test du module llm_client"""

    print("=" * 60)
    print("🧪 TEST LLM CLIENT - Groq API")
    print("=" * 60)

    # Vérifier la clé API
    if not GROQ_API_KEY:
        print("\n⚠️ GROQ_API_KEY non configurée!")
        print("Crée un fichier .env avec :")
        print("GROQ_API_KEY=gsk_xxxxxxxxx")
        print("\nObtiens ta clé sur : https://console.groq.com/keys")
        exit(1)

    print(f"\n✅ Clé API configurée (modèle: {GROQ_MODEL})")

    # Test simple
    print("\n📝 Test appel simple...")
    response = call_groq("Dis 'Bonjour Sonalyze!' en une phrase.", temperature=0.5)
    if response:
        print(f"   Réponse: {response[:100]}...")
    else:
        print("   ❌ Échec de l'appel")
        exit(1)

    # Test avec données simulées
    print("\n📊 Test avec données simulées...")

    fake_analysis = {
        "global": {
            "note_globale": "D",
            "db_mean": 46.5,
            "db_min": 28.0,
            "db_max": 77.0,
            "duration_hours": 21.6,
        },
        "day_night": {"jour": {"mean": 51.0}, "nuit": {"mean": 41.0}},
        "sounds": {
            "top_20": [
                {
                    "label": "Vehicle",
                    "percentage": 64.9,
                    "avg_score": 0.15,
                    "family": "circulation",
                },
                {
                    "label": "Music",
                    "percentage": 22.3,
                    "avg_score": 0.12,
                    "family": "musique",
                },
                {
                    "label": "Speech",
                    "percentage": 12.1,
                    "avg_score": 0.08,
                    "family": "voisinage",
                },
            ],
            "families_pct": {
                "circulation": 64.9,
                "musique": 22.3,
                "voisinage": 12.1,
            },
            "classification": {
                "normaux": ["Speech"],
                "exceptionnels": ["Vehicle"],
                "problematiques_frequents": ["Vehicle"],
            },
        },
    }

    fake_logement = {
        "type": "Appartement",
        "etage": "3ème",
        "piece": "Salon",
        "ville": "Pantin (93500)",
        "nom": "M. Dupont",
        "adresse": "14 rue Montgolfier",
    }

    print("\n--- Interprétation de la note ---")
    interpretation = generate_grade_interpretation(fake_analysis, fake_logement)
    print(interpretation[:500] + "..." if len(interpretation) > 500 else interpretation)

    print("\n--- Analyse des sons ---")
    sounds = generate_sounds_analysis(fake_analysis)
    print(sounds[:500] + "..." if len(sounds) > 500 else sounds)

    print("\n--- Recommandations (extrait) ---")
    reco = generate_recommendations(fake_analysis, fake_logement)
    if "fenetre" in reco:
        print(f"Fenêtre - Priorité: {reco['fenetre'].get('priorite', 'N/A')}")
        print(f"  Problème: {reco['fenetre'].get('probleme', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ TEST LLM CLIENT TERMINÉ")
    print("=" * 60)
