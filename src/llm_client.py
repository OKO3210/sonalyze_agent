"""
=============================================================================
SONALYZE AGENT - Client LLM (Groq API)
=============================================================================
Génère les textes d'interprétation et recommandations pour le rapport DPS.
Utilise Llama 3.3 70B via Groq (rapide et gratuit).

Auteur: Équipe Patria
Date: Décembre 2024
=============================================================================
"""

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"


# =============================================================================
# CLIENT GROQ
# =============================================================================

def get_groq_client():
    """
    Initialise le client Groq.
    
    Returns:
        Client Groq ou None si non configuré
    """
    if not GROQ_API_KEY:
        print("GROQ_API_KEY non configurée dans .env")
        return None

    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except ImportError:
        print("Package 'groq' non installé. Run: pip install groq")
        return None


def call_groq(
    prompt: str, 
    system_prompt: str = None, 
    temperature: float = 0.3
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
        print(f"Erreur Groq API: {e}")
        return None


# =============================================================================
# PROMPTS SYSTÈME
# =============================================================================

SYSTEM_ACOUSTICIAN = """Tu es un expert acousticien pédagogue spécialisé dans le diagnostic sonore des logements.
Tu expliques les résultats de manière claire et accessible pour des particuliers non-experts.
Tu es rassurant mais honnête. Tu donnes des conseils pratiques et actionnables.
Tu réponds TOUJOURS en français.
Tu évites le jargon technique, ou tu l'expliques simplement quand c'est nécessaire.
Tu ne mets PAS d'emojis dans tes réponses."""


# =============================================================================
# GÉNÉRATION DE CONTENU
# =============================================================================

def generate_grade_interpretation(
    analysis: Dict[str, Any], 
    logement_info: Dict[str, Any]
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

    note = global_stats.get("note_globale", "D")
    db_mean = global_stats.get("db_mean", 45)
    db_min = global_stats.get("db_min", 30)
    db_max = global_stats.get("db_max", 70)
    duration = global_stats.get("duration_hours", 24)
    jour_mean = day_night.get("jour", {}).get("mean", 50)
    nuit_mean = day_night.get("nuit", {}).get("mean", 40)

    prompt = f"""Voici les résultats d'un diagnostic de performance sonore (DPS) :

LOGEMENT :
- Type : {logement_info.get('type', 'Appartement')}
- Étage : {logement_info.get('etage', 'Non précisé')}
- Pièce analysée : {logement_info.get('piece', 'Salon')}
- Ville : {logement_info.get('ville', 'Non précisée')}

RÉSULTATS :
- Note globale : {note}
- Niveau sonore moyen : {db_mean:.1f} dB
- Niveau minimum : {db_min:.1f} dB
- Niveau maximum : {db_max:.1f} dB
- Durée d'enregistrement : {duration:.1f} heures

JOUR vs NUIT :
- Moyenne jour (7h-22h) : {jour_mean:.1f} dB
- Moyenne nuit (22h-7h) : {nuit_mean:.1f} dB

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
- Ne mets PAS d'emojis

Format : Texte simple, pas de bullet points, pas de titres, pas d'emojis."""

    result = call_groq(prompt, SYSTEM_ACOUSTICIAN)

    if not result:
        confort = (
            "correct" if note in ['A', 'B', 'C'] 
            else "moyen" if note == 'D' 
            else "insuffisant"
        )
        return f"""Votre logement obtient la note {note} avec un niveau sonore moyen de {db_mean:.0f} dB. Cette note correspond à un confort acoustique {confort}.

La différence entre le jour ({jour_mean:.0f} dB) et la nuit ({nuit_mean:.0f} dB) montre une variation normale liée aux activités extérieures.

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
    top_sounds = analysis.get("sounds", {}).get("top_5", [])
    families = analysis.get("sounds", {}).get("families_pct", {})
    classified = analysis.get("sounds", {}).get("classification", {})

    sounds_text = "\n".join([
        f"- {s['label']}: {s['percentage']:.1f}% du temps, "
        f"{s['avg_score']:.3f} confiance, famille: {s['family']}"
        for s in top_sounds[:8]
    ])

    families_text = "\n".join([
        f"- {family}: {pct:.1f}%"
        for family, pct in sorted(
            families.items(), key=lambda x: x[1], reverse=True
        )[:5]
    ])

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
- Ne mets PAS d'emojis

Format : Texte simple, pas de bullet points, pas de titres, pas d'emojis."""

    result = call_groq(prompt, SYSTEM_ACOUSTICIAN)

    if not result:
        main_sound = top_sounds[0]["label"] if top_sounds else "circulation"
        return f"""L'analyse sur 24h révèle que la source sonore principale est "{main_sound}". Les bruits détectés proviennent majoritairement de l'environnement extérieur.

Les sons normaux du quotidien (voix, électroménager) représentent une part acceptable des nuisances. En revanche, certains bruits extérieurs méritent une attention particulière.

Consultez les graphiques ci-dessous pour une vue détaillée par heure et par type de bruit."""

    return result


def generate_recommendations(
    analysis: Dict[str, Any], 
    logement_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Génère des recommandations personnalisées par élément du logement.
    Inclut les points positifs, les problèmes et les solutions avec coûts.

    Args:
        analysis: Résultat de aggregator.generate_full_analysis()
        logement_info: Infos du logement

    Returns:
        Dict avec recommandations structurées par catégorie
    """
    global_stats = analysis.get("global", {})
    families = analysis.get("sounds", {}).get("families_pct", {})

    note = global_stats.get("note_globale", "D")
    
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
    "points_positifs": "ce qui est bien actuellement (1-2 phrases)",
    "probleme": "description courte du problème si existant",
    "solutions": [
      {{
        "nom": "nom solution",
        "description": "explication courte",
        "cout_min": 50,
        "cout_max": 100,
        "impact": "réduction dB estimée",
        "difficulte": "facile/moyen/difficile"
      }}
    ]
  }},
  "mur": {{ ... }},
  "porte": {{ ... }},
  "plafond": {{ ... }},
  "sol": {{ ... }},
  "aeration": {{ ... }}
}}

IMPORTANT :
- cout_min et cout_max sont des NOMBRES (pas de texte, pas de €)
- points_positifs doit toujours contenir quelque chose de positif
- Si note A-C : mettre plus de points positifs, moins de problèmes
- Si note D-E : équilibré
- Si note F-G : plus de problèmes, solutions prioritaires

Réponds UNIQUEMENT avec le JSON, sans texte avant/après."""

    result = call_groq(prompt, SYSTEM_ACOUSTICIAN, temperature=0.2)

    if result:
        try:
            json_str = result.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            json_str = json_str.strip()

            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    return get_default_recommendations(note, families)


def get_default_recommendations(
    note: str, 
    families: Dict[str, float]
) -> Dict[str, Any]:
    """
    Recommandations par défaut si l'API échoue.
    Inclut points positifs et coûts détaillés.
    
    Args:
        note: Note globale (A-G)
        families: Pourcentages par famille de sons
    
    Returns:
        Dict structuré des recommandations
    """
    is_circulation = families.get("circulation", 0) > 30
    is_voisinage = families.get("voisinage", 0) > 20
    is_good = note in ["A", "B", "C"]
    is_severe = note in ["E", "F", "G"]

    # Fenêtres
    fenetre_solutions: List[Dict] = [
        {
            "nom": "Joints d'étanchéité",
            "description": "Remplacement des joints usés autour des fenêtres",
            "cout_min": 50,
            "cout_max": 100,
            "impact": "-5 à -10 dB",
            "difficulte": "facile",
        },
        {
            "nom": "Rideaux phoniques",
            "description": "Installation de rideaux épais à propriétés acoustiques",
            "cout_min": 100,
            "cout_max": 200,
            "impact": "-3 à -5 dB",
            "difficulte": "facile",
        },
    ]
    if is_severe:
        fenetre_solutions.append({
            "nom": "Double ou triple vitrage",
            "description": "Remplacement complet des fenêtres par du vitrage performant",
            "cout_min": 3000,
            "cout_max": 6000,
            "impact": "-15 à -25 dB",
            "difficulte": "difficile",
        })

    # Murs
    mur_solutions: List[Dict] = [
        {
            "nom": "Panneaux acoustiques décoratifs",
            "description": "Panneaux muraux absorbants, faciles à installer",
            "cout_min": 100,
            "cout_max": 300,
            "impact": "-3 à -5 dB",
            "difficulte": "facile",
        },
    ]
    if is_severe:
        mur_solutions.append({
            "nom": "Doublage isolant",
            "description": "Ajout d'une contre-cloison avec isolant acoustique",
            "cout_min": 2000,
            "cout_max": 5000,
            "impact": "-10 à -15 dB",
            "difficulte": "difficile",
        })

    # Plafond
    plafond_solutions: List[Dict] = []
    if is_voisinage or is_severe:
        plafond_solutions.append({
            "nom": "Faux plafond acoustique",
            "description": "Installation d'un plafond suspendu avec isolant",
            "cout_min": 3000,
            "cout_max": 8000,
            "impact": "-15 à -25 dB",
            "difficulte": "difficile",
        })

    return {
        "fenetre": {
            "priorite": "haute" if is_circulation else "moyenne" if not is_good else "basse",
            "points_positifs": (
                "Vos fenêtres offrent déjà une isolation correcte pour ce type de logement."
                if is_good else
                "La structure des fenêtres permet d'envisager des améliorations simples et efficaces."
            ),
            "probleme": (
                "Légère transmission du bruit extérieur" if is_good else
                "Transmission du bruit extérieur à améliorer" if not is_severe else
                "Transmission importante du bruit extérieur nécessitant une intervention"
            ),
            "solutions": fenetre_solutions,
        },
        "mur": {
            "priorite": "moyenne" if is_voisinage else "basse",
            "points_positifs": (
                "Les murs présentent une masse suffisante pour bloquer la majorité des bruits."
                if is_good else
                "La configuration des murs permet d'ajouter des solutions d'absorption efficaces."
            ),
            "probleme": (
                "Transmission latérale modérée" if is_voisinage else
                "Isolation murale standard, améliorable si besoin"
            ),
            "solutions": mur_solutions,
        },
        "plafond": {
            "priorite": "haute" if is_voisinage else "basse",
            "points_positifs": (
                "Le plafond ne présente pas de transmission excessive de bruits d'impact."
                if not is_voisinage else
                "La hauteur sous plafond permet d'envisager une solution d'isolation."
            ),
            "probleme": (
                "Bruits d'impact du dessus à traiter" if is_voisinage else
                "Aucun problème majeur détecté"
            ),
            "solutions": plafond_solutions if plafond_solutions else [{
                "nom": "Aucune intervention nécessaire",
                "description": "Le plafond offre une isolation satisfaisante",
                "cout_min": 0,
                "cout_max": 0,
                "impact": "-",
                "difficulte": "-",
            }],
        },
        "sol": {
            "priorite": "basse",
            "points_positifs": "Le revêtement de sol actuel contribue à l'absorption des bruits intérieurs.",
            "probleme": "Transmission possible vers le dessous",
            "solutions": [
                {
                    "nom": "Tapis épais",
                    "description": "Ajout de tapis ou moquette pour absorber les bruits d'impact",
                    "cout_min": 100,
                    "cout_max": 300,
                    "impact": "-3 à -5 dB",
                    "difficulte": "facile",
                },
                {
                    "nom": "Sous-couche acoustique",
                    "description": "Installation sous le revêtement existant",
                    "cout_min": 500,
                    "cout_max": 1500,
                    "impact": "-10 à -15 dB",
                    "difficulte": "moyen",
                },
            ],
        },
        "porte": {
            "priorite": "moyenne",
            "points_positifs": "Les portes assurent une séparation correcte entre les pièces.",
            "probleme": "Passage du son par les interstices",
            "solutions": [
                {
                    "nom": "Bas de porte",
                    "description": "Installation d'un joint bas de porte",
                    "cout_min": 20,
                    "cout_max": 50,
                    "impact": "-3 à -5 dB",
                    "difficulte": "facile",
                },
                {
                    "nom": "Porte acoustique",
                    "description": "Remplacement par une porte à isolation renforcée",
                    "cout_min": 500,
                    "cout_max": 1500,
                    "impact": "-10 à -20 dB",
                    "difficulte": "moyen",
                },
            ],
        },
        "aeration": {
            "priorite": "basse",
            "points_positifs": "Le système de ventilation fonctionne correctement.",
            "probleme": "Les entrées d'air peuvent laisser passer le bruit extérieur",
            "solutions": [
                {
                    "nom": "Entrées d'air acoustiques",
                    "description": "Remplacement par des grilles à chicanes acoustiques",
                    "cout_min": 50,
                    "cout_max": 150,
                    "impact": "-5 à -10 dB",
                    "difficulte": "moyen",
                }
            ],
        },
    }


def calculate_total_costs(recommendations: Dict[str, Any]) -> Dict[str, int]:
    """
    Calcule les coûts totaux min et max de toutes les solutions.
    
    Args:
        recommendations: Dict des recommandations
    
    Returns:
        {"min": total_min, "max": total_max}
    """
    total_min = 0
    total_max = 0
    
    for category, data in recommendations.items():
        if isinstance(data, dict):
            solutions = data.get("solutions", [])
            for sol in solutions:
                if isinstance(sol, dict):
                    total_min += sol.get("cout_min", 0) or 0
                    total_max += sol.get("cout_max", 0) or 0
    
    return {"min": total_min, "max": total_max}


def generate_summary_email(
    analysis: Dict[str, Any], 
    logement_info: Dict[str, Any],
    cost_range: Dict[str, int] = None,
    selected_solutions: List[str] = None
) -> str:
    """
    Génère un email de synthèse pour le client avec fourchette de coûts.

    Args:
        analysis: Résultat de aggregator.generate_full_analysis()
        logement_info: Infos du logement
        cost_range: {"min": X, "max": Y} fourchette de coûts
        selected_solutions: Liste des solutions sélectionnées (optionnel)

    Returns:
        Texte de l'email
    """
    global_stats = analysis.get("global", {})
    note = global_stats.get("note_globale", "D")
    db = global_stats.get("db_mean", 45)
    
    cost_text = ""
    if cost_range:
        cost_min = cost_range.get("min", 0)
        cost_max = cost_range.get("max", 0)
        if cost_max > 0:
            cost_text = f"\nEstimation budgétaire pour l'ensemble des améliorations : entre {cost_min:,} € et {cost_max:,} €.".replace(",", " ")

    solutions_text = ""
    if selected_solutions:
        solutions_text = f"\nSolutions retenues : {', '.join(selected_solutions)}."

    prompt = f"""Rédige un email de synthèse pour un client ayant reçu son diagnostic acoustique.

INFOS :
- Nom : {logement_info.get('nom', 'Client')}
- Adresse : {logement_info.get('adresse', 'Non précisée')}
- Note obtenue : {note}
- Niveau moyen : {db:.0f} dB
{cost_text}
{solutions_text}

L'email doit :
- Remercier pour la confiance
- Résumer la note en 1 phrase
- Mentionner 2-3 points positifs du logement
- Donner 2-3 conseils prioritaires
- Inclure la fourchette de coûts si disponible
- Proposer un accompagnement (optionnel)
- Être chaleureux et professionnel
- Ne PAS mettre d'emojis

Format : Email prêt à envoyer (avec Objet:, puis le corps)."""

    result = call_groq(prompt, SYSTEM_ACOUSTICIAN)

    if not result:
        cost_line = ""
        if cost_range and cost_range.get("max", 0) > 0:
            cost_line = f"\nL'estimation budgétaire pour améliorer votre confort acoustique se situe entre {cost_range['min']:,} € et {cost_range['max']:,} €.\n".replace(",", " ")
        
        return f"""Objet : Votre diagnostic de performance sonore - Note {note}

Bonjour,

Merci d'avoir fait confiance à Sonalyze pour votre diagnostic acoustique.

Votre logement obtient la note {note} avec un niveau sonore moyen de {db:.0f} dB. Cette analyse sur 24 heures nous permet de vous proposer des recommandations adaptées à votre situation.

Points positifs identifiés :
- La structure générale du logement offre une base correcte pour l'isolation
- Les variations jour/nuit restent dans des plages gérables
- Des solutions simples et abordables peuvent améliorer significativement votre confort
{cost_line}
Nous vous invitons à consulter le rapport complet ci-joint pour découvrir nos recommandations personnalisées.

N'hésitez pas à nous contacter pour toute question ou pour être mis en relation avec des artisans qualifiés.

Cordialement,
L'équipe Sonalyze"""

    return result


def generate_all_interpretations(
    analysis: Dict[str, Any], 
    logement_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Génère tous les textes d'interprétation en un seul appel.

    Args:
        analysis: Résultat de aggregator.generate_full_analysis()
        logement_info: Infos du logement

    Returns:
        Dict avec tous les textes générés
    """
    print("Generation des interpretations IA...")

    print("  - Interpretation de la note...")
    grade_interpretation = generate_grade_interpretation(analysis, logement_info)

    print("  - Analyse des sources sonores...")
    sounds_analysis = generate_sounds_analysis(analysis)

    print("  - Recommandations personnalisees...")
    recommendations = generate_recommendations(analysis, logement_info)
    
    print("  - Calcul des couts...")
    cost_range = calculate_total_costs(recommendations)

    print("  - Email de synthese...")
    summary_email = generate_summary_email(
        analysis, 
        logement_info, 
        cost_range
    )

    print("Interpretations generees")

    return {
        "grade_interpretation": grade_interpretation,
        "sounds_analysis": sounds_analysis,
        "recommendations": recommendations,
        "cost_range": cost_range,
        "summary_email": summary_email,
    }


# =============================================================================
# TEST DU MODULE
# =============================================================================

if __name__ == "__main__":
    """Test du module llm_client"""

    print("=" * 60)
    print("TEST LLM CLIENT - Groq API")
    print("=" * 60)

    if not GROQ_API_KEY:
        print("\nGROQ_API_KEY non configuree!")
        print("Cree un fichier .env avec :")
        print("GROQ_API_KEY=gsk_xxxxxxxxx")
        print("\nObtiens ta cle sur : https://console.groq.com/keys")
        exit(1)

    print(f"\nCle API configuree (modele: {GROQ_MODEL})")

    print("\nTest appel simple...")
    response = call_groq("Dis 'Bonjour Sonalyze!' en une phrase.", temperature=0.5)
    if response:
        print(f"   Reponse: {response[:100]}...")
    else:
        print("   Echec de l'appel")
        exit(1)

    print("\nTest recommandations par defaut...")
    reco = get_default_recommendations("D", {"circulation": 50, "voisinage": 10})
    
    print("\nVerification structure:")
    for category, data in reco.items():
        print(f"\n  {category.upper()}:")
        print(f"    - Priorite: {data.get('priorite')}")
        print(f"    - Points positifs: {data.get('points_positifs', '')[:50]}...")
        print(f"    - Probleme: {data.get('probleme', '')[:50]}...")
        solutions = data.get("solutions", [])
        for sol in solutions:
            cout = f"{sol.get('cout_min', 0)}-{sol.get('cout_max', 0)} EUR"
            print(f"    - Solution: {sol.get('nom')} | Cout: {cout}")
    
    print("\nTest calcul couts...")
    costs = calculate_total_costs(reco)
    print(f"   Fourchette totale: {costs['min']} - {costs['max']} EUR")
    
    print("\nTest termine")
