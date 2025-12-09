"""
=============================================================================
SONALYZE AGENT - Chargement et Validation des Données
=============================================================================
Ce module gère :
1. Le chargement du fichier JSON brut du boîtier Sonalyze
2. La validation de la structure des données
3. La conversion en DataFrame pandas pour traitement

Pourquoi un module séparé ?
- Séparation des responsabilités (Single Responsibility Principle)
- Facilite les tests unitaires
- Permet de changer le format d'entrée sans toucher au reste du code

Format JSON attendu (chaque élément du tableau) :
{
    "box_id": "pi3",
    "timestamp": "2025-12-04 09:43:44",
    "LAeq_segment_dB": 45.38,
    "LAeq_rating": "C",
    "Lmin_dB": -57.96,
    "Lmax_dB": 61.80,
    "LPeak_dB": 61.80,
    "L10_dB": 49.63,
    "L50_dB": 41.61,
    "L90_dB": 26.88,
    "SNR_dB": "Not Computed",
    "top_5_labels": ["Vehicle", "Music", "Car", "Engine", "Cacophony"],
    "top_5_probs": [0.043, 0.040, 0.019, 0.016, 0.012]
}
=============================================================================
"""

import json
import pandas as pd
from pathlib import Path
from typing import Union, Optional
from datetime import datetime


# =============================================================================
# CONSTANTES DE VALIDATION
# =============================================================================

# Champs obligatoires dans chaque segment JSON
REQUIRED_FIELDS = [
    "box_id",
    "timestamp",
    "LAeq_segment_dB",
    "LAeq_rating",
    "top_5_labels",
    "top_5_probs",
]

# Champs optionnels (peuvent être absents ou invalides)
OPTIONAL_FIELDS = [
    "Lmin_dB",
    "Lmax_dB",
    "LPeak_dB",
    "L10_dB",
    "L50_dB",
    "L90_dB",
    "SNR_dB",
]

# Notes valides pour LAeq_rating
VALID_RATINGS = ["A", "B", "C", "D", "E", "F", "G"]


# =============================================================================
# CLASSE PRINCIPALE
# =============================================================================


class DataLoader:
    """
    Classe responsable du chargement et de la validation des données JSON.

    Utilisation:
        loader = DataLoader("data/exemple.json")
        df = loader.load()

        # Ou avec validation détaillée
        loader = DataLoader("data/exemple.json")
        if loader.validate():
            df = loader.to_dataframe()
    """

    def __init__(self, filepath: Union[str, Path]):
        """
        Initialise le loader avec le chemin du fichier.

        Args:
            filepath: Chemin vers le fichier JSON (str ou Path)
        """
        self.filepath = Path(filepath)
        self.raw_data: Optional[list] = None
        self.validation_errors: list = []
        self.validation_warnings: list = []

    def load_json(self) -> list:
        """
        Charge le fichier JSON brut.

        Returns:
            Liste des segments (dictionnaires)

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            json.JSONDecodeError: Si le JSON est mal formé
        """
        # Vérifie que le fichier existe
        if not self.filepath.exists():
            raise FileNotFoundError(f"Fichier non trouvé : {self.filepath}")

        # Vérifie l'extension
        if self.filepath.suffix.lower() != ".json":
            raise ValueError(
                f"Extension invalide : {self.filepath.suffix} (attendu: .json)"
            )

        # Charge le JSON
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.raw_data = json.load(f)

        # Vérifie que c'est une liste
        if not isinstance(self.raw_data, list):
            raise ValueError("Le JSON doit contenir une liste de segments")

        print(f"✅ Fichier chargé : {len(self.raw_data)} segments")
        return self.raw_data

    def validate(self) -> bool:
        """
        Valide la structure et le contenu des données.

        Returns:
            True si les données sont valides (erreurs critiques = 0)

        Note:
            Les erreurs sont stockées dans self.validation_errors
            Les avertissements dans self.validation_warnings
        """
        # Charge les données si pas encore fait
        if self.raw_data is None:
            self.load_json()

        self.validation_errors = []
        self.validation_warnings = []

        # Vérifie que la liste n'est pas vide
        if len(self.raw_data) == 0:
            self.validation_errors.append("Le fichier JSON est vide")
            return False

        # Valide chaque segment
        for i, segment in enumerate(self.raw_data):
            self._validate_segment(segment, index=i)

        # Résumé de validation
        if self.validation_errors:
            print(f"❌ Validation échouée : {len(self.validation_errors)} erreurs")
            for error in self.validation_errors[:5]:  # Affiche les 5 premières
                print(f"   - {error}")
            if len(self.validation_errors) > 5:
                print(f"   ... et {len(self.validation_errors) - 5} autres erreurs")
            return False

        if self.validation_warnings:
            print(
                f"⚠️  Validation OK avec {len(self.validation_warnings)} avertissements"
            )
        else:
            print(f"✅ Validation OK : {len(self.raw_data)} segments valides")

        return True

    def _validate_segment(self, segment: dict, index: int) -> None:
        """
        Valide un segment individuel.

        Args:
            segment: Dictionnaire représentant un segment
            index: Index du segment dans la liste (pour les messages d'erreur)
        """
        # Vérifie que c'est un dictionnaire
        if not isinstance(segment, dict):
            self.validation_errors.append(
                f"Segment {index} : n'est pas un dictionnaire"
            )
            return

        # Vérifie les champs obligatoires
        for field in REQUIRED_FIELDS:
            if field not in segment:
                self.validation_errors.append(
                    f"Segment {index} : champ '{field}' manquant"
                )

        # Vérifie le format du timestamp
        if "timestamp" in segment:
            try:
                datetime.strptime(segment["timestamp"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                self.validation_warnings.append(
                    f"Segment {index} : format timestamp invalide '{segment['timestamp']}'"
                )

        # Vérifie que LAeq_segment_dB est un nombre valide
        if "LAeq_segment_dB" in segment:
            db_value = segment["LAeq_segment_dB"]
            if not isinstance(db_value, (int, float)):
                self.validation_errors.append(
                    f"Segment {index} : LAeq_segment_dB n'est pas un nombre"
                )
            elif db_value < 0 or db_value > 150:
                self.validation_warnings.append(
                    f"Segment {index} : LAeq_segment_dB hors limites ({db_value})"
                )

        # Vérifie que LAeq_rating est valide
        if "LAeq_rating" in segment:
            rating = segment["LAeq_rating"]
            if rating not in VALID_RATINGS:
                self.validation_warnings.append(
                    f"Segment {index} : LAeq_rating invalide '{rating}'"
                )

        # Vérifie top_5_labels et top_5_probs
        if "top_5_labels" in segment and "top_5_probs" in segment:
            labels = segment["top_5_labels"]
            probs = segment["top_5_probs"]

            if not isinstance(labels, list) or not isinstance(probs, list):
                self.validation_errors.append(
                    f"Segment {index} : top_5_labels/probs doivent être des listes"
                )
            elif len(labels) != len(probs):
                self.validation_warnings.append(
                    f"Segment {index} : top_5_labels et top_5_probs n'ont pas la même taille"
                )

        # Vérifie les valeurs Lmin_dB aberrantes (négatifs extrêmes = erreur capteur)
        if "Lmin_dB" in segment:
            lmin = segment["Lmin_dB"]
            if isinstance(lmin, (int, float)) and lmin < -100:
                self.validation_warnings.append(
                    f"Segment {index} : Lmin_dB aberrant ({lmin}), sera ignoré"
                )

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convertit les données brutes en DataFrame pandas.

        Returns:
            DataFrame avec les colonnes :
            - Toutes les colonnes du JSON
            - timestamp_dt : datetime parsé
            - hour : heure (0-23)
            - is_night : True si entre 22h et 7h
            - top_label : label du son principal (top_5_labels[0])
            - top_prob : probabilité du son principal (top_5_probs[0])

        Raises:
            ValueError: Si les données n'ont pas été chargées ou validées
        """
        if self.raw_data is None:
            raise ValueError("Données non chargées. Appelez load_json() d'abord.")

        # Crée le DataFrame de base
        df = pd.DataFrame(self.raw_data)

        # Convertit le timestamp en datetime
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

        # Extrait l'heure
        df["hour"] = df["timestamp_dt"].dt.hour

        # Détermine si c'est la nuit (22h-7h)
        df["is_night"] = df["hour"].apply(lambda h: h >= 22 or h < 7)

        # Extrait le son principal et sa probabilité
        df["top_label"] = df["top_5_labels"].apply(lambda x: x[0] if x else None)
        df["top_prob"] = df["top_5_probs"].apply(lambda x: x[0] if x else 0)

        # Nettoie les Lmin_dB aberrants (remplace par NaN)
        if "Lmin_dB" in df.columns:
            df.loc[df["Lmin_dB"] < -100, "Lmin_dB"] = None

        print(f"✅ DataFrame créé : {len(df)} lignes, {len(df.columns)} colonnes")
        return df

    def load(self) -> pd.DataFrame:
        """
        Méthode pratique : charge, valide et retourne le DataFrame.

        Returns:
            DataFrame prêt à être utilisé

        Raises:
            ValueError: Si la validation échoue
        """
        self.load_json()

        if not self.validate():
            raise ValueError(
                f"Validation échouée avec {len(self.validation_errors)} erreurs. "
                "Consultez loader.validation_errors pour plus de détails."
            )

        return self.to_dataframe()

    def get_summary(self) -> dict:
        """
        Retourne un résumé rapide des données chargées.

        Returns:
            Dictionnaire avec les statistiques de base
        """
        if self.raw_data is None:
            self.load_json()

        df = self.to_dataframe()

        return {
            "total_segments": len(df),
            "duration_hours": len(df) * 9 / 3600,  # ~9 sec par segment
            "date_start": df["timestamp_dt"].min().strftime("%Y-%m-%d %H:%M"),
            "date_end": df["timestamp_dt"].max().strftime("%Y-%m-%d %H:%M"),
            "box_ids": df["box_id"].unique().tolist(),
            "ratings_distribution": df["LAeq_rating"].value_counts().to_dict(),
            "db_mean": round(df["LAeq_segment_dB"].mean(), 2),
            "db_min": round(df["LAeq_segment_dB"].min(), 2),
            "db_max": round(df["LAeq_segment_dB"].max(), 2),
        }


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================


def load_json_file(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Fonction raccourcie pour charger un fichier JSON.

    Args:
        filepath: Chemin vers le fichier JSON

    Returns:
        DataFrame pandas

    Example:
        df = load_json_file("data/exemple.json")
    """
    loader = DataLoader(filepath)
    return loader.load()


def validate_json_file(filepath: Union[str, Path]) -> tuple[bool, list, list]:
    """
    Valide un fichier JSON sans le charger complètement.

    Args:
        filepath: Chemin vers le fichier JSON

    Returns:
        Tuple (is_valid, errors, warnings)
    """
    loader = DataLoader(filepath)
    is_valid = loader.validate()
    return is_valid, loader.validation_errors, loader.validation_warnings


# =============================================================================
# TEST DU MODULE (exécution directe)
# =============================================================================

if __name__ == "__main__":
    """
    Test du module quand exécuté directement.
    Usage : python src/data_loader.py
    """
    import sys

    # Chemin par défaut ou passé en argument
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "data/dps_analysis_pi3_exemple.json"

    print(f"\n{'='*60}")
    print(f"TEST DATA_LOADER - {filepath}")
    print(f"{'='*60}\n")

    try:
        # Crée le loader
        loader = DataLoader(filepath)

        # Charge et valide
        df = loader.load()

        # Affiche le résumé
        print(f"\n{'='*60}")
        print("RÉSUMÉ DES DONNÉES")
        print(f"{'='*60}")

        summary = loader.get_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")

        # Affiche les premières lignes
        print(f"\n{'='*60}")
        print("APERÇU (5 premières lignes)")
        print(f"{'='*60}")
        print(
            df[
                ["timestamp", "LAeq_segment_dB", "LAeq_rating", "top_label", "top_prob"]
            ].head()
        )

    except Exception as e:
        print(f"❌ Erreur : {e}")
        sys.exit(1)
