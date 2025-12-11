"""
=============================================================================
SONALYZE AGENT - Agrégation des Statistiques
=============================================================================
Calcule toutes les métriques nécessaires au rapport DPS :
- Statistiques globales (moyenne, min, max)
- Statistiques jour/nuit
- Distribution des notes A-G
- Top sons détectés (global + par période)
- Répartition par famille de sons (avec notes)
- Données pour la heatmap 24h

Auteur: Équipe Patria
Date: Décembre 2024
=============================================================================
"""

from collections import Counter
from typing import Any, Dict, List

import numpy as np
import pandas as pd

# Imports locaux (même dossier src/)
from config import (
    FILTERING_PARAMS,
    SOUND_FAMILIES,
    get_note_from_db,
    get_sound_family,
    is_sound_normal,
    is_sound_problematic,
)


# =============================================================================
# STATISTIQUES GLOBALES
# =============================================================================

def calculate_global_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule les statistiques globales sur l'ensemble des données.

    Args:
        df: DataFrame issu de DataLoader

    Returns:
        dict: Statistiques globales (mean, min, max, note, durée, etc.)
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

    Args:
        df: DataFrame avec colonne 'is_night'

    Returns:
        dict: {"jour": {...}, "nuit": {...}}
    """
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


# =============================================================================
# DISTRIBUTION DES NOTES
# =============================================================================

def calculate_rating_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """
    Calcule la distribution des notes A-G.

    Args:
        df: DataFrame avec colonne 'LAeq_rating'

    Returns:
        dict: {"A": 120, "B": 340, "C": 4985, ...}
    """
    counts = df["LAeq_rating"].value_counts().to_dict()
    all_ratings = ["A", "B", "C", "D", "E", "F", "G"]
    return {rating: counts.get(rating, 0) for rating in all_ratings}


def calculate_rating_percentages(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcule les pourcentages de chaque note.

    Args:
        df: DataFrame

    Returns:
        dict: {"A": 1.4, "B": 3.9, "C": 57.5, ...}
    """
    distribution = calculate_rating_distribution(df)
    total = sum(distribution.values())

    if total == 0:
        return {k: 0.0 for k in distribution}

    return {k: round(v / total * 100, 1) for k, v in distribution.items()}


# =============================================================================
# ANALYSE DES SONS
# =============================================================================

def calculate_top_sounds(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Identifie les sons les plus fréquemment détectés.

    Args:
        df: DataFrame
        top_n: Nombre de sons à retourner (défaut: 5)

    Returns:
        list: Liste de dicts avec label, count, percentage, family, 
              is_problematic, avg_db, note
    """
    if len(df) == 0:
        return []

    label_counts = df["top_label"].value_counts()
    label_scores = df.groupby("top_label")["top_prob"].mean()
    label_db = df.groupby("top_label")["LAeq_segment_dB"].mean()

    results = []
    total = len(df)

    for label in label_counts.head(top_n).index:
        count = label_counts[label]
        avg_db = label_db[label]
        note = get_note_from_db(avg_db)
        
        results.append({
            "label": label,
            "count": int(count),
            "percentage": round(count / total * 100, 1),
            "avg_score": round(label_scores[label], 3),
            "avg_db": round(avg_db, 1),
            "note": note,
            "family": get_sound_family(label),
            "is_problematic": is_sound_problematic(label),
            "is_normal": is_sound_normal(label),
        })

    return results


def calculate_top_sounds_by_period(
    df: pd.DataFrame, 
    period: str, 
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Identifie les sons les plus fréquents pour une période (jour ou nuit).

    Args:
        df: DataFrame
        period: 'jour' ou 'nuit'
        top_n: Nombre de sons à retourner (défaut: 5)

    Returns:
        list: Liste de dicts avec stats par son
    """
    if period == "jour":
        df_period = df[~df["is_night"]]
    else:
        df_period = df[df["is_night"]]
    
    if len(df_period) == 0:
        return []
    
    return calculate_top_sounds(df_period, top_n)


# =============================================================================
# FAMILLES DE SONS
# =============================================================================

def calculate_family_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """
    Répartition des sons par famille (pour le camembert).

    Args:
        df: DataFrame

    Returns:
        dict: {"circulation": 4500, "voisinage": 2000, ...}
    """
    df_copy = df.copy()
    df_copy["family"] = df_copy["top_label"].apply(get_sound_family)
    return df_copy["family"].value_counts().to_dict()


def calculate_family_percentages(df: pd.DataFrame) -> Dict[str, float]:
    """
    Pourcentages par famille de sons.

    Args:
        df: DataFrame

    Returns:
        dict: {"circulation": 65.2, ...}
    """
    distribution = calculate_family_distribution(df)
    total = sum(distribution.values())

    if total == 0:
        return {}

    return {k: round(v / total * 100, 1) for k, v in distribution.items()}


def calculate_family_by_period(
    df: pd.DataFrame, 
    period: str
) -> Dict[str, Dict[str, Any]]:
    """
    Répartition des sons par famille pour une période (jour ou nuit).
    Inclut la note moyenne par famille.

    Args:
        df: DataFrame
        period: 'jour' ou 'nuit'

    Returns:
        dict: {
            "circulation": {"count": 450, "percentage": 65.2, "avg_db": 52.3, "note": "D"},
            ...
        }
    """
    if period == "jour":
        df_period = df[~df["is_night"]].copy()
    else:
        df_period = df[df["is_night"]].copy()
    
    if len(df_period) == 0:
        return {}
    
    df_period["family"] = df_period["top_label"].apply(get_sound_family)
    
    family_stats = df_period.groupby("family").agg({
        "LAeq_segment_dB": ["count", "mean"]
    }).reset_index()
    
    family_stats.columns = ["family", "count", "avg_db"]
    total = family_stats["count"].sum()
    
    result = {}
    for _, row in family_stats.iterrows():
        result[row["family"]] = {
            "count": int(row["count"]),
            "percentage": round(row["count"] / total * 100, 1),
            "avg_db": round(row["avg_db"], 1),
            "note": get_note_from_db(row["avg_db"])
        }
    
    # Trie par pourcentage décroissant
    result = dict(sorted(
        result.items(), 
        key=lambda x: x[1]["percentage"], 
        reverse=True
    ))
    
    return result


# =============================================================================
# DONNÉES TEMPORELLES
# =============================================================================

def calculate_hourly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Statistiques par heure (pour la heatmap).

    Args:
        df: DataFrame

    Returns:
        DataFrame avec colonnes: hour, db_mean, db_max, db_min, count, dominant_sound
    """
    hourly = (
        df.groupby("hour")
        .agg({
            "LAeq_segment_dB": ["mean", "max", "min", "count"],
            "top_label": lambda x: x.mode()[0] if len(x) > 0 else None,
        })
        .reset_index()
    )

    hourly.columns = ["hour", "db_mean", "db_max", "db_min", "count", "dominant_sound"]

    hourly["db_mean"] = hourly["db_mean"].round(1)
    hourly["db_max"] = hourly["db_max"].round(1)
    hourly["db_min"] = hourly["db_min"].round(1)

    return hourly


def build_heatmap_data(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Construit la matrice pour la heatmap Catégories × Heures.

    Args:
        df: DataFrame
        top_n: Nombre de sons à inclure

    Returns:
        DataFrame pivot (sons en lignes, heures en colonnes)
    """
    top_sounds = df["top_label"].value_counts().head(top_n).index.tolist()
    df_filtered = df[df["top_label"].isin(top_sounds)].copy()

    pivot = pd.pivot_table(
        df_filtered,
        values="LAeq_segment_dB",
        index="top_label",
        columns="hour",
        aggfunc="count",
        fill_value=0,
    )

    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False)
    pivot = pivot.drop("total", axis=1)

    return pivot


# =============================================================================
# DÉTECTION D'ÉVÉNEMENTS
# =============================================================================

def identify_sound_events(
    df: pd.DataFrame, 
    min_consecutive: int = 3
) -> List[Dict]:
    """
    Identifie les événements sonores (son répété plusieurs fois de suite).

    Un événement = même son détecté min_consecutive fois consécutives.

    Args:
        df: DataFrame
        min_consecutive: Nombre minimum de répétitions

    Returns:
        list: Liste d'événements avec start_time, end_time, label, duration, avg_db
    """
    events = []
    current_label = None
    current_segments = []

    for _, row in df.iterrows():
        label = row["top_label"]

        if label == current_label:
            current_segments.append(row)
        else:
            # Fin de l'événement précédent
            if current_label and len(current_segments) >= min_consecutive:
                events.append({
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
                })

            current_label = label
            current_segments = [row]

    # Traite le dernier événement
    if current_label and len(current_segments) >= min_consecutive:
        events.append({
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
        })

    return events


# =============================================================================
# CLASSIFICATION POUR RAPPORT
# =============================================================================

def classify_sounds_for_report(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Classe les sons en catégories pour le rapport.

    Args:
        df: DataFrame

    Returns:
        dict: {
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
            if percentage > 5:
                problematiques_frequents.append(label)
        else:
            if percentage > 10:
                normaux.append(label)
            else:
                exceptionnels.append(label)

    return {
        "normaux": normaux[:10],
        "exceptionnels": exceptionnels[:10],
        "problematiques_frequents": problematiques_frequents,
    }


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def generate_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère l'analyse complète en un seul appel.

    C'est la fonction principale à utiliser.

    Args:
        df: DataFrame issu de DataLoader

    Returns:
        dict: Dictionnaire complet avec toutes les statistiques
    """
    return {
        "global": calculate_global_stats(df),
        "day_night": calculate_day_night_stats(df),
        "ratings": {
            "distribution": calculate_rating_distribution(df),
            "percentages": calculate_rating_percentages(df),
        },
        "sounds": {
            # Top 5 global
            "top_5": calculate_top_sounds(df, 5),
            # Top 5 par période (JOUR / NUIT)
            "top_5_jour": calculate_top_sounds_by_period(df, "jour", 5),
            "top_5_nuit": calculate_top_sounds_by_period(df, "nuit", 5),
            # Familles globales
            "families": calculate_family_distribution(df),
            "families_pct": calculate_family_percentages(df),
            # Familles par période avec notes (JOUR / NUIT)
            "families_jour": calculate_family_by_period(df, "jour"),
            "families_nuit": calculate_family_by_period(df, "nuit"),
            # Classification pour le rapport
            "classification": classify_sounds_for_report(df),
        },
        "hourly": calculate_hourly_stats(df).to_dict("records"),
        "events": identify_sound_events(df)[:50],
    }


# =============================================================================
# TEST DU MODULE
# =============================================================================

if __name__ == "__main__":
    from data_loader import DataLoader

    print("\n" + "=" * 60)
    print("TEST AGGREGATOR")
    print("=" * 60 + "\n")

    loader = DataLoader("../data/dps_analysis_pi3_exemple.json")
    df = loader.load()

    analysis = generate_full_analysis(df)

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

    print("\n☀️ TOP 5 SONS - JOUR")
    print("-" * 40)
    for sound in analysis["sounds"]["top_5_jour"]:
        status = "🔴" if sound["is_problematic"] else "🟢"
        print(f"  {status} {sound['label']}: {sound['percentage']}% | "
              f"{sound['avg_db']}dB | Note {sound['note']}")

    print("\n🌙 TOP 5 SONS - NUIT")
    print("-" * 40)
    for sound in analysis["sounds"]["top_5_nuit"]:
        status = "🔴" if sound["is_problematic"] else "🟢"
        print(f"  {status} {sound['label']}: {sound['percentage']}% | "
              f"{sound['avg_db']}dB | Note {sound['note']}")

    print("\n✅ Test terminé")
