"""
=============================================================================
SONALYZE AGENT - Configuration et Constantes
=============================================================================
Ce fichier centralise toutes les constantes utilisées dans le projet :
- Échelle DPS (notes A-G et seuils en dB)
- Seuils de confort par type de pièce
- Familles de sons pour la classification
- Paramètres de filtrage des données

Pourquoi centraliser ?
- Facilite la maintenance (modifier une valeur à un seul endroit)
- Améliore la lisibilité du code
- Permet de documenter les choix métier
=============================================================================
"""

# =============================================================================
# ÉCHELLE DPS OFFICIELLE
# =============================================================================
# Source : Rapport_DPS.pdf page 4
# Cette échelle définit la correspondance entre niveau sonore et note

DPS_SCALE = {
    "A": {
        "max_db": 20,
        "label": "Conversation à voix basse, chambre à coucher",
        "color": "#00A651",  # Vert foncé
        "description": "Logement extrêmement performant",
    },
    "B": {
        "max_db": 30,
        "label": "Bureau calme",
        "color": "#92D050",  # Vert clair
        "description": "Très bon confort acoustique",
    },
    "C": {
        "max_db": 45,
        "label": "Machine à laver",
        "color": "#FFFF00",  # Jaune
        "description": "Confort acoustique acceptable",
    },
    "D": {
        "max_db": 60,
        "label": "Centre commercial, aspirateur, automobile",
        "color": "#FFC000",  # Orange
        "description": "Confort acoustique moyen",
    },
    "E": {
        "max_db": 80,
        "label": "Automobile, moto",
        "color": "#FF6600",  # Orange foncé
        "description": "Confort acoustique insuffisant",
    },
    "F": {
        "max_db": 100,
        "label": "Musique puissance maximale",
        "color": "#FF0000",  # Rouge
        "description": "Passoire phonique",
    },
    "G": {
        "max_db": 120,
        "label": "Concert, marteau-piqueur, avion",
        "color": "#C00000",  # Rouge foncé
        "description": "Logement très peu performant",
    },
}


# =============================================================================
# SEUILS DE CONFORT PAR TYPE DE PIÈCE
# =============================================================================
# Source : Rapport_DPS.pdf page 2 (commentaires jaunes)
# Ces seuils définissent ce qui est considéré comme bon/moyen/insuffisant
# selon le type de pièce

ROOM_THRESHOLDS = {
    "chambre": {
        "bon": 25,  # < 25 dB = BON (sommeil optimal)
        "moyen": 35,  # 25-35 dB = MOYEN
        "insuffisant": 45,  # > 35 dB = INSUFFISANT
    },
    "salon": {"bon": 35, "moyen": 45, "insuffisant": 55},
    "bureau": {"bon": 35, "moyen": 45, "insuffisant": 55},
    "cuisine": {"bon": 45, "moyen": 55, "insuffisant": 65},
    "salle_de_bain": {"bon": 45, "moyen": 55, "insuffisant": 65},
    # Valeurs par défaut pour les autres pièces
    "default": {"bon": 40, "moyen": 50, "insuffisant": 60},
}


# =============================================================================
# CLASSIFICATION DES SONS
# =============================================================================
# Mapping des labels du modèle AST (527 classes) vers des familles lisibles
# Source : Config_AI_Classification.json + expertise acoustique

SOUND_FAMILIES = {
    # --- Bruits de circulation (extérieurs) ---
    "circulation": [
        "Vehicle",
        "Car",
        "Engine",
        "Motorcycle",
        "Truck",
        "Traffic noise, roadway noise",
        "Accelerating, revving, vroom",
        "Motor vehicle (road)",
        "Bus",
        "Car passing by",
        "Race car, auto racing",
        "Tire squeal",
        "Skidding",
        "Vehicle horn, car horn, honking",
        "Emergency vehicle",
        "Ambulance (siren)",
        "Police car (siren)",
        "Fire engine, fire truck (siren)",
    ],
    # --- Bruits de transport (train, avion) ---
    "transport": [
        "Train",
        "Rail transport",
        "Train whistle",
        "Train horn",
        "Subway, metro, underground",
        "Aircraft",
        "Aircraft engine",
        "Jet engine",
        "Helicopter",
        "Fixed-wing aircraft, airplane",
    ],
    # --- Bruits de voisinage (voix, activités humaines) ---
    "voisinage": [
        "Speech",
        "Male speech, man speaking",
        "Female speech, woman speaking",
        "Child speech, kid speaking",
        "Conversation",
        "Narration, monologue",
        "Shout",
        "Yell",
        "Screaming",
        "Children shouting",
        "Laughter",
        "Crying, sobbing",
        "Baby cry, infant cry",
        "Crowd",
        "Chatter",
        "Hubbub, speech noise, speech babble",
        "Children playing",
        "Walk, footsteps",
        "Run",
        "Clapping",
        "Applause",
    ],
    # --- Musique et sons récréatifs ---
    "musique": [
        "Music",
        "Singing",
        "Musical instrument",
        "Pop music",
        "Rock music",
        "Hip hop music",
        "Classical music",
        "Jazz",
        "Electronic music",
        "Guitar",
        "Piano",
        "Drum",
        "Drum kit",
        "Bass guitar",
    ],
    # --- Bruits d'intérieur (ambiance) ---
    "interieur": [
        "Inside, small room",
        "Inside, large room or hall",
        "Inside, public space",
        "Door",
        "Knock",
        "Slam",
        "Sliding door",
        "Cupboard open or close",
        "Drawer open or close",
        "Squeak",
        "Creak",
    ],
    # --- Électroménager ---
    "electromenager": [
        "Vacuum cleaner",
        "Blender",
        "Microwave oven",
        "Hair dryer",
        "Mechanical fan",
        "Air conditioning",
        "Washing machine",
        "Dishes, pots, and pans",
        "Cutlery, silverware",
        "Chopping (food)",
        "Frying (food)",
        "Water tap, faucet",
        "Toilet flush",
        "Boiling",
    ],
    # --- Nature et environnement ---
    "nature": [
        "Bird",
        "Bird vocalization, bird call, bird song",
        "Chirp, tweet",
        "Rain",
        "Raindrop",
        "Rain on surface",
        "Thunder",
        "Thunderstorm",
        "Wind",
        "Rustling leaves",
        "Water",
        "Stream",
        "Ocean",
        "Waves, surf",
    ],
    # --- Travaux et outils ---
    "travaux": [
        "Drill",
        "Hammer",
        "Sawing",
        "Power tool",
        "Jackhammer",
        "Sanding",
        "Filing (rasp)",
        "Chainsaw",
        "Lawn mower",
    ],
    # --- Alertes et alarmes ---
    "alertes": [
        "Alarm",
        "Alarm clock",
        "Siren",
        "Smoke detector, smoke alarm",
        "Fire alarm",
        "Car alarm",
        "Buzzer",
        "Telephone bell ringing",
        "Ringtone",
    ],
    # --- Animaux domestiques ---
    "animaux": ["Dog", "Bark", "Cat", "Meow", "Purr", "Domestic animals, pets"],
}

# Sons considérés comme "normaux" (acceptables au quotidien)
NORMAL_SOUNDS = [
    "Bird",
    "Bird vocalization, bird call, bird song",
    "Chirp, tweet",
    "Rain",
    "Raindrop",
    "Wind",
    "Rustling leaves",
    "Music",
    "Singing",
    "Speech",
    "Conversation",
    "Water",
    "Stream",
    "Clock",
    "Tick-tock",
]

# Sons considérés comme "problématiques" (nuisances)
PROBLEMATIC_SOUNDS = [
    "Vehicle",
    "Car",
    "Truck",
    "Motorcycle",
    "Traffic noise, roadway noise",
    "Aircraft",
    "Jet engine",
    "Train",
    "Drill",
    "Jackhammer",
    "Hammer",
    "Power tool",
    "Chainsaw",
    "Alarm",
    "Siren",
    "Car alarm",
    "Smoke detector, smoke alarm",
    "Screaming",
    "Shout",
    "Children shouting",
    "Baby cry, infant cry",
    "Dog",
    "Bark",
]


# =============================================================================
# PARAMÈTRES DE FILTRAGE DES DONNÉES
# =============================================================================
# Seuils pour nettoyer et filtrer les données brutes du capteur

FILTERING_PARAMS = {
    # Score minimum AST pour considérer un son comme détecté
    # En dessous, c'est du bruit statistique (1/527 classes = 0.0019)
    "min_score_threshold": 0.01,
    # Nombre minimum de détections consécutives pour valider un événement
    # Augmente la fiabilité en éliminant les faux positifs ponctuels
    "min_consecutive_detections": 3,
    # Valeur minimale de dB acceptée (en dessous = erreur de mesure)
    "min_valid_db": 0,
    # Valeur maximale de dB acceptée (au-dessus = erreur de mesure)
    "max_valid_db": 130,
    # Heures définissant le jour (pour stats jour/nuit)
    "day_start_hour": 7,  # 7h00
    "day_end_hour": 22,  # 22h00
}


# =============================================================================
# PARAMÈTRES LLM (GROQ)
# =============================================================================

LLM_CONFIG = {
    "model": "llama-3.3-70b-versatile",  # Modèle Groq à utiliser
    "temperature": 0.3,  # Basse = réponses plus cohérentes et factuelles
    "max_tokens": 2000,  # Limite de tokens par réponse
}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================


def get_note_from_db(db_value: float) -> str:
    """
    Détermine la note DPS (A-G) à partir d'un niveau sonore en dB.

    Args:
        db_value: Niveau sonore en dB(A)

    Returns:
        Note de A à G selon l'échelle DPS

    Example:
        >>> get_note_from_db(35)
        'C'
        >>> get_note_from_db(65)
        'E'
    """
    for note, params in DPS_SCALE.items():
        if db_value <= params["max_db"]:
            return note
    return "G"  # Par défaut si > 120 dB


def get_room_status(db_value: float, room_type: str) -> str:
    """
    Détermine le statut (bon/moyen/insuffisant) pour une pièce donnée.

    Args:
        db_value: Niveau sonore en dB(A)
        room_type: Type de pièce (chambre, salon, etc.)

    Returns:
        Statut : "bon", "moyen" ou "insuffisant"
    """
    thresholds = ROOM_THRESHOLDS.get(room_type, ROOM_THRESHOLDS["default"])

    if db_value <= thresholds["bon"]:
        return "bon"
    elif db_value <= thresholds["moyen"]:
        return "moyen"
    else:
        return "insuffisant"


def get_sound_family(label: str) -> str:
    """
    Trouve la famille d'un son à partir de son label AST.

    Args:
        label: Label du son (ex: "Vehicle", "Speech")

    Returns:
        Nom de la famille ou "autres" si non trouvé
    """
    for family, labels in SOUND_FAMILIES.items():
        if label in labels:
            return family
    return "autres"


def is_sound_problematic(label: str) -> bool:
    """
    Vérifie si un son est considéré comme problématique.

    Args:
        label: Label du son

    Returns:
        True si le son est dans la liste des sons problématiques
    """
    return label in PROBLEMATIC_SOUNDS


def is_sound_normal(label: str) -> bool:
    """
    Vérifie si un son est considéré comme normal/acceptable.

    Args:
        label: Label du son

    Returns:
        True si le son est dans la liste des sons normaux
    """
    return label in NORMAL_SOUNDS
