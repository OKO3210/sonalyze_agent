"""
=============================================================================
SONALYZE AGENT - Package Principal
=============================================================================
Agent IA d'interprétation pour Sonalyze (diagnostic de performance sonore).

Modules:
- config: Configuration, constantes DPS, familles de sons
- data_loader: Chargement et validation des fichiers JSON
- aggregator: Calcul des statistiques et analyses
- charts: Génération des graphiques Plotly
- llm_client: Interprétation IA via Groq API

Auteur: Équipe Patria (Hackathon La Forge 2024)
=============================================================================
"""

# Version du package
__version__ = "1.0.0"
__author__ = "Équipe Patria"

# Configuration et constantes
from .config import (
    DPS_SCALE,
    SOUND_FAMILIES,
    THRESHOLDS,
    get_note_from_db,
    get_sound_family,
    is_sound_normal,
    is_sound_problematic,
)

# Chargement des données
from .data_loader import DataLoader, load_json_file

# Analyse et agrégation
from .aggregator import (
    generate_full_analysis,
    calculate_global_stats,
    calculate_day_night_stats,
    calculate_top_sounds,
    calculate_family_distribution,
)

# Graphiques
from .charts import (
    generate_all_charts,
    create_dps_gauge,
    create_family_pie,
    create_sounds_heatmap,
)

# Client LLM
from .llm_client import (
    generate_all_interpretations,
    generate_grade_interpretation,
    generate_recommendations,
)

# Export public
__all__ = [
    # Version
    "__version__",
    "__author__",
    # Config
    "DPS_SCALE",
    "SOUND_FAMILIES",
    "THRESHOLDS",
    "get_note_from_db",
    "get_sound_family",
    "is_sound_normal",
    "is_sound_problematic",
    # Data
    "DataLoader",
    "load_json_file",
    # Aggregator
    "generate_full_analysis",
    "calculate_global_stats",
    "calculate_day_night_stats",
    "calculate_top_sounds",
    "calculate_family_distribution",
    # Charts
    "generate_all_charts",
    "create_dps_gauge",
    "create_family_pie",
    "create_sounds_heatmap",
    # LLM
    "generate_all_interpretations",
    "generate_grade_interpretation",
    "generate_recommendations",
]
