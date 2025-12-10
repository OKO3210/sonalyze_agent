"""
=============================================================================
SONALYZE AGENT - Agrégation des Statistiques
=============================================================================
Calcule toutes les métriques nécessaires au rapport DPS :
- Statistiques globales (moyenne, min, max)
- Statistiques jour/nuit
- Distribution des notes A-G
- Top sons détectés
- Répartition par famille de sons
- Données pour la heatmap 24h
=============================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from collections import Counter

# Import de notre config
from src.config import (
    SOUND_FAMILIES,
    FILTERING_PARAMS,
    get_sound_family,
    get_note_from_db,
    is_sound_problematic,
    is_sound_normal,
)


def calculate_global_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les statistiques globales sur l'ensemble des données.

    Args:
        df: DataFrame issu de DataLoader

    Returns:
        Dictionnaire avec les stats globales
    """
    return {
        "total_segments": len(df),
        "duration_hours": round(len(df) * 9 / 3600, 2),
        "date_start": df["timestamp_dt"].min().strftime("%Y-%m-%d %H:%M"),
        "date_end": df["timestamp_dt"].max().strftime("%Y-%m-%d %H:%M"),
        "db_mean": round(df["LAeq_segment_dB"].mean(), 1),
        "db_min": round(df["LAeq_segment_dB"].min(), 1),
        "db_max": round(df["LAeq_segment_dB"].max(), 1),
        "db_median": round(df["LAeq_segment_dB"].median(), 1),
        "note_globale": get_note_from_db(df["LAeq_segment_dB"].mean()),
    }


def calculate_day_night_stats(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calcule les statistiques séparées jour/nuit.

    Jour = 7h à 22h
    Nuit = 22h à 7h

    Returns:
        {"jour": {...}, "nuit": {...}}
    """
    # Sépare les données
    df_jour = df[~df["is_night"]]
    df_nuit = df[df["is_night"]]

    def stats_for_period(data: pd.DataFrame) -> Dict[str, float]:
        if len(data) == 0:
            return {"mean": None, "min": None, "max": None, "count": 0}
        return {
            "mean": round(data["LAeq_segment_dB"].mean(), 1),
            "min": round(data["LAeq_segment_dB"].min(), 1),
            "max": round(data["LAeq_segment_dB"].max(), 1),
            "count": len(data),
        }

    return {
        "jour": stats_for_period(df_jour),
        "nuit": stats_for_period(df_nuit),
    }


def calculate_rating_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """
    Calcule la distribution des notes A-G.

    Returns:
        {"A": 120, "B": 340, "C": 4985, ...}
    """
    # Compte les occurrences de chaque note
    counts = df["LAeq_rating"].value_counts().to_dict()

    # Assure que toutes les notes sont présentes (même à 0)
    all_ratings = ["A", "B", "C", "D", "E", "F", "G"]
    return {rating: counts.get(rating, 0) for rating in all_ratings}


def calculate_rating_percentages(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcule les pourcentages de chaque note.

    Returns:
        {"A": 1.4, "B": 3.9, "C": 57.5, ...}
    """
    distribution = calculate_rating_distribution(df)
    total = sum(distribution.values())

    if total == 0:
        return {k: 0.0 for k in distribution}

    return {k: round(v / total * 100, 1) for k, v in distribution.items()}


def calculate_top_sounds(df: pd.DataFrame, top_n: int = 20) -> List[Dict[str, Any]]:
    """
    Identifie les sons les plus fréquemment détectés.

    Args:
        df: DataFrame
        top_n: Nombre de sons à retourner

    Returns:
        Liste de dicts avec label, count, percentage, family, is_problematic
    """
    # Compte tous les labels (top_label = son principal de chaque segment)
    label_counts = df["top_label"].value_counts()

    # Calcule aussi le score moyen par label
    label_scores = df.groupby("top_label")["top_prob"].mean()

    results = []
    total = len(df)

    for label in label_counts.head(top_n).index:
        count = label_counts[label]
        results.append(
            {
                "label": label,
                "count": int(count),
                "percentage": round(count / total * 100, 1),
                "avg_score": round(label_scores[label], 3),
                "family": get_sound_family(label),
                "is_problematic": is_sound_problematic(label),
                "is_normal": is_sound_normal(label),
            }
        )

    return results


def calculate_family_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """
    Répartition des sons par famille (pour le camembert).

    Returns:
        {"circulation": 4500, "voisinage": 2000, ...}
    """
    # Associe chaque segment à une famille
    df_copy = df.copy()
    df_copy["family"] = df_copy["top_label"].apply(get_sound_family)

    # Compte par famille
    return df_copy["family"].value_counts().to_dict()


def calculate_family_percentages(df: pd.DataFrame) -> Dict[str, float]:
    """
    Pourcentages par famille de sons.
    """
    distribution = calculate_family_distribution(df)
    total = sum(distribution.values())

    if total == 0:
        return {}

    return {k: round(v / total * 100, 1) for k, v in distribution.items()}


def calculate_hourly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Statistiques par heure (pour la heatmap).

    Returns:
        DataFrame avec colonnes: hour, db_mean, db_max, dominant_sound
    """
    hourly = (
        df.groupby("hour")
        .agg(
            {
                "LAeq_segment_dB": ["mean", "max", "min", "count"],
                "top_label": lambda x: x.mode()[0] if len(x) > 0 else None,
            }
        )
        .reset_index()
    )

    # Flatten les colonnes multi-index
    hourly.columns = ["hour", "db_mean", "db_max", "db_min", "count", "dominant_sound"]

    # Arrondit les valeurs
    hourly["db_mean"] = hourly["db_mean"].round(1)
    hourly["db_max"] = hourly["db_max"].round(1)
    hourly["db_min"] = hourly["db_min"].round(1)

    return hourly


def build_heatmap_data(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Construit la matrice pour la heatmap Catégories × Heures.

    Lignes = Top N sons détectés
    Colonnes = Heures (0-23)
    Valeurs = Nombre d'occurrences

    Returns:
        DataFrame pivot (sons en lignes, heures en colonnes)
    """
    # Récupère les top N sons
    top_sounds = df["top_label"].value_counts().head(top_n).index.tolist()

    # Filtre sur ces sons uniquement
    df_filtered = df[df["top_label"].isin(top_sounds)].copy()

    # Crée le pivot table
    pivot = pd.pivot_table(
        df_filtered,
        values="LAeq_segment_dB",
        index="top_label",
        columns="hour",
        aggfunc="count",
        fill_value=0,
    )

    # Réordonne les lignes par fréquence totale
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False)
    pivot = pivot.drop("total", axis=1)

    return pivot


def identify_sound_events(df: pd.DataFrame, min_consecutive: int = 3) -> List[Dict]:
    """
    Identifie les événements sonores (son répété plusieurs fois de suite).

    Un événement = même son détecté min_consecutive fois consécutives.
    Augmente la fiabilité de la détection.

    Returns:
        Liste d'événements avec start_time, end_time, label, duration, avg_db
    """
    events = []
    current_label = None
    current_start = None
    current_segments = []

    for _, row in df.iterrows():
        label = row["top_label"]

        if label == current_label:
            # Continue l'événement en cours
            current_segments.append(row)
        else:
            # Fin de l'événement précédent
            if current_label and len(current_segments) >= min_consecutive:
                events.append(
                    {
                        "label": current_label,
                        "start_time": current_segments[0]["timestamp"],
                        "end_time": current_segments[-1]["timestamp"],
                        "duration_segments": len(current_segments),
                        "duration_seconds": len(current_segments) * 9,
                        "avg_db": round(
                            np.mean([s["LAeq_segment_dB"] for s in current_segments]), 1
                        ),
                        "max_db": round(
                            max([s["LAeq_segment_dB"] for s in current_segments]), 1
                        ),
                        "avg_score": round(
                            np.mean([s["top_prob"] for s in current_segments]), 3
                        ),
                        "family": get_sound_family(current_label),
                        "is_problematic": is_sound_problematic(current_label),
                    }
                )

            # Démarre un nouvel événement
            current_label = label
            current_segments = [row]

    # Traite le dernier événement
    if current_label and len(current_segments) >= min_consecutive:
        events.append(
            {
                "label": current_label,
                "start_time": current_segments[0]["timestamp"],
                "end_time": current_segments[-1]["timestamp"],
                "duration_segments": len(current_segments),
                "duration_seconds": len(current_segments) * 9,
                "avg_db": round(
                    np.mean([s["LAeq_segment_dB"] for s in current_segments]), 1
                ),
                "max_db": round(
                    max([s["LAeq_segment_dB"] for s in current_segments]), 1
                ),
                "avg_score": round(
                    np.mean([s["top_prob"] for s in current_segments]), 3
                ),
                "family": get_sound_family(current_label),
                "is_problematic": is_sound_problematic(current_label),
            }
        )

    return events


def classify_sounds_for_report(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Classe les sons en catégories pour le rapport.

    Returns:
        {
            "normaux": ["Music", "Speech", ...],
            "exceptionnels": ["Vehicle", "Drill", ...],
            "problematiques_frequents": [...],
        }
    """
    top_sounds = calculate_top_sounds(df, top_n=30)

    normaux = []
    exceptionnels = []
    problematiques_frequents = []

    for sound in top_sounds:
        label = sound["label"]
        percentage = sound["percentage"]

        if sound["is_normal"]:
            normaux.append(label)
        elif sound["is_problematic"]:
            exceptionnels.append(label)
            if percentage > 5:  # Plus de 5% du temps = fréquent
                problematiques_frequents.append(label)
        else:
            # Sons neutres (ni normaux ni problématiques)
            if percentage > 10:
                normaux.append(label)
            else:
                exceptionnels.append(label)

    return {
        "normaux": normaux[:10],
        "exceptionnels": exceptionnels[:10],
        "problematiques_frequents": problematiques_frequents,
    }


def generate_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère l'analyse complète en un seul appel.

    C'est la fonction principale à utiliser.

    Returns:
        Dictionnaire complet avec toutes les statistiques
    """
    return {
        "global": calculate_global_stats(df),
        "day_night": calculate_day_night_stats(df),
        "ratings": {
            "distribution": calculate_rating_distribution(df),
            "percentages": calculate_rating_percentages(df),
        },
        "sounds": {
            "top_20": calculate_top_sounds(df, 20),
            "families": calculate_family_distribution(df),
            "families_pct": calculate_family_percentages(df),
            "classification": classify_sounds_for_report(df),
        },
        "hourly": calculate_hourly_stats(df).to_dict("records"),
        "events": identify_sound_events(df)[:50],  # Limite à 50 événements
    }


# =============================================================================
# TEST DU MODULE
# =============================================================================

if __name__ == "__main__":
    import json
    from src.data_loader import DataLoader

    print("\n" + "=" * 60)
    print("TEST AGGREGATOR")
    print("=" * 60 + "\n")

    # Charge les données
    loader = DataLoader("data/dps_analysis_pi3_exemple.json")
    df = loader.load()

    # Génère l'analyse complète
    analysis = generate_full_analysis(df)

    # Affiche les résultats
    print("📊 STATISTIQUES GLOBALES")
    print("-" * 40)
    for k, v in analysis["global"].items():
        print(f"  {k}: {v}")

    print("\n🌙 JOUR / NUIT")
    print("-" * 40)
    print(f"  Jour : {analysis['day_night']['jour']['mean']} dB moyen")
    print(f"  Nuit : {analysis['day_night']['nuit']['mean']} dB moyen")

    print("\n📈 DISTRIBUTION DES NOTES")
    print("-" * 40)
    for note, pct in analysis["ratings"]["percentages"].items():
        bar = "█" * int(pct / 2)
        print(f"  {note}: {bar} {pct}%")

    print("\n🔊 TOP 10 SONS")
    print("-" * 40)
    for sound in analysis["sounds"]["top_20"][:10]:
        status = "⚠️" if sound["is_problematic"] else "✅"
        print(
            f"  {status} {sound['label']}: {sound['percentage']}% ({sound['family']})"
        )

    print("\n📁 RÉPARTITION PAR FAMILLE")
    print("-" * 40)
    for family, pct in analysis["sounds"]["families_pct"].items():
        print(f"  {family}: {pct}%")

    print("\n🎯 ÉVÉNEMENTS DÉTECTÉS (5 premiers)")
    print("-" * 40)
    for event in analysis["events"][:5]:
        print(f"  {event['label']}: {event['duration_seconds']}s à {event['avg_db']}dB")
