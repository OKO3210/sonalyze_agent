# 🏗️ Architecture Technique - Agent IA Sonalyze

## Vue d'ensemble

L'Agent IA Sonalyze transforme les données brutes d'un capteur acoustique en un **diagnostic de performance sonore (DPS)** compréhensible et actionnable.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   BOÎTIER IoT   │────▶│   AGENT IA      │────▶│   RAPPORT DPS   │
│  (Capteur son)  │     │  (Notre code)   │     │  (PDF + Web)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     JSON brut           Analyse + LLM          Interprétation
```

---

## 🔧 Stack Technique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Langage** | Python 3.11+ | Backend principal |
| **Data** | Pandas | Manipulation des données |
| **Visualisation** | Plotly | Graphiques interactifs |
| **LLM** | Groq API (Llama 3.3 70B) | Interprétation IA |
| **Interface** | Streamlit | Application web |
| **PDF** | ReportLab | Génération rapport |

---

## 📁 Structure du Projet

```
sonalyze_agent/
├── src/
│   ├── config.py          # Constantes et paramètres
│   ├── data_loader.py     # Chargement/validation JSON
│   ├── aggregator.py      # Calculs statistiques
│   ├── charts.py          # Génération graphiques
│   ├── llm_client.py      # Interprétation IA (Groq)
│   └── app.py             # Interface Streamlit
├── data/
│   └── *.json             # Fichiers de test
├── output/
│   └── *.html             # Graphiques exportés
├── docs/
│   └── *.md               # Documentation
└── requirements.txt
```

---

## 🔄 Pipeline de Données

### Étape 1 : Données d'entrée (JSON)

Le boîtier Sonalyze génère un fichier JSON avec ~8000 segments (1 segment = ~9 secondes).

```json
{
  "box_id": "pi3",
  "timestamp": "2025-12-04 09:43:44",
  "LAeq_segment_dB": 45.38,
  "LAeq_rating": "C",
  "Lmin_dB": 26.88,
  "Lmax_dB": 61.80,
  "top_5_labels": ["Vehicle", "Music", "Car", "Engine", "Speech"],
  "top_5_probs": [0.043, 0.040, 0.019, 0.016, 0.012]
}
```

**Modèle de classification** : Audio Spectrogram Transformer (AST)
- 527 classes de sons (AudioSet)
- Précision : ~95% sur les classes principales

### Étape 2 : Chargement et Validation (`data_loader.py`)

```python
from src.data_loader import DataLoader

loader = DataLoader("data/fichier.json")
df = loader.load()  # DataFrame Pandas
```

**Validations effectuées :**
- Structure JSON conforme
- Timestamps valides
- dB dans plage [0-130]
- Probabilités dans [0-1]

**Enrichissement automatique :**
- `hour` : Extraction de l'heure
- `is_night` : True si 22h-7h
- `top_label` : Son principal détecté

### Étape 3 : Agrégation (`aggregator.py`)

```python
from src.aggregator import generate_full_analysis

analysis = generate_full_analysis(df)
```

**Calculs effectués :**

| Métrique | Description |
|----------|-------------|
| `global.db_mean` | Niveau sonore moyen (dB) |
| `global.note_globale` | Note DPS (A-G) |
| `day_night` | Stats séparées jour/nuit |
| `sounds.top_5` | 5 sons les plus fréquents |
| `sounds.top_5_jour/nuit` | Top 5 par période |
| `sounds.families_jour/nuit` | Répartition par famille |
| `ratings.distribution` | Distribution A-G |

### Étape 4 : Visualisation (`charts.py`)

```python
from src.charts import generate_all_charts

charts = generate_all_charts(analysis, df)
```

**Graphiques générés :**

| Graphique | Description |
|-----------|-------------|
| `gauge` | Jauge de performance (style DPE) |
| `rating_bars` | Distribution des notes |
| `day_night` | Comparaison jour/nuit |
| `top_sounds_jour/nuit` | Top 5 sons séparés |
| `family_pie_jour/nuit` | Camemberts familles |
| `sounds_heatmap` | Heatmap 24h × sons |

### Étape 5 : Interprétation IA (`llm_client.py`)

```python
from src.llm_client import generate_all_interpretations

interpretations = generate_all_interpretations(analysis, logement_info)
```

**Contenus générés par le LLM :**

1. **Interprétation de la note** : Explication pédagogique du score
2. **Analyse des sources** : Identification des nuisances principales
3. **Recommandations** : Solutions par élément (fenêtre, mur, plafond...)
4. **Email de synthèse** : Résumé pour le client

---

## 🧠 Classification des Sons

### Familles de sons

Le modèle AST détecte 527 types de sons. Nous les regroupons en **11 familles** :

| Famille | Exemples | Caractère |
|---------|----------|-----------|
| `circulation` | Vehicle, Car, Truck | 🔴 Problématique |
| `transport` | Train, Aircraft | 🔴 Problématique |
| `voisinage` | Speech, Footsteps | 🟡 Modéré |
| `musique` | Music, Guitar, Piano | 🟡 Modéré |
| `interieur` | Door, Knock, Squeak | 🟢 Normal |
| `electromenager` | Vacuum, Blender | 🟡 Modéré |
| `nature` | Bird, Rain, Wind | 🟢 Positif |
| `travaux` | Drill, Hammer | 🔴 Problématique |
| `alertes` | Alarm, Siren | 🔴 Problématique |
| `animaux` | Dog, Cat | 🟡 Modéré |
| `autres` | Non classifié | - |

### Échelle DPS (A-G)

| Note | Seuil (dB) | Description |
|------|-----------|-------------|
| **A** | ≤ 20 | Exceptionnel - Silence quasi-total |
| **B** | ≤ 30 | Très bon - Très calme |
| **C** | ≤ 45 | Bon - Acceptable |
| **D** | ≤ 60 | Moyen - Modéré |
| **E** | ≤ 80 | Insuffisant - Bruyant |
| **F** | ≤ 100 | Très insuffisant |
| **G** | > 100 | Critique - Dangereux |

---

## 🔌 API LLM (Groq)

### Pourquoi Groq ?

- **Gratuit** : Tier gratuit généreux
- **Rapide** : ~200ms par requête
- **Performant** : Llama 3.3 70B = qualité GPT-4

### Configuration

```env
# .env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx
```

### Prompts utilisés

**System prompt (acousticien expert) :**
```
Tu es un expert acousticien pédagogue spécialisé dans le diagnostic 
sonore des logements. Tu expliques de manière claire et accessible.
Tu réponds TOUJOURS en français.
```

**Paramètres :**
- `temperature: 0.3` (réponses cohérentes)
- `max_tokens: 2000`
- `model: llama-3.3-70b-versatile`

---

## 📊 Format de Sortie

### Structure `analysis` complète

```python
{
    "global": {
        "db_mean": 46.5,
        "db_min": 28.0,
        "db_max": 77.0,
        "note_globale": "D",
        "duration_hours": 21.6
    },
    "day_night": {
        "jour": {"mean": 51.0, "min": 35.0, "max": 77.0},
        "nuit": {"mean": 41.0, "min": 28.0, "max": 65.0}
    },
    "sounds": {
        "top_5": [
            {"label": "Vehicle", "percentage": 64.9, "avg_db": 52.3, "note": "D"},
            ...
        ],
        "top_5_jour": [...],
        "top_5_nuit": [...],
        "families_jour": {
            "circulation": {"count": 450, "percentage": 65.2, "avg_db": 52.3, "note": "D"}
        },
        "families_nuit": {...}
    },
    "ratings": {
        "distribution": {"A": 120, "B": 340, "C": 4985, "D": 2800, ...},
        "percentages": {"A": 1.4, "B": 3.9, "C": 57.5, ...}
    }
}
```

---

## 🚀 Déploiement

### Local (développement)

```bash
cd sonalyze_agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run src/app.py
```

### Production (suggéré)

| Service | Usage |
|---------|-------|
| **Streamlit Cloud** | Interface web |
| **Railway** | Backend API |
| **Vercel** | Frontend statique |

---

## 📈 Métriques de Performance

| Métrique | Valeur |
|----------|--------|
| Temps chargement JSON (8665 segments) | ~0.5s |
| Temps analyse complète | ~1s |
| Temps génération graphiques | ~2s |
| Temps appel LLM (4 requêtes) | ~3-5s |
| **Total pipeline** | **~7-10s** |

---

## 🔒 Sécurité

- Clé API stockée dans `.env` (non versionné)
- Validation des données en entrée
- Pas de données personnelles stockées
- RGPD : Anonymisation des adresses possible

---

*Document créé pour le hackathon La Forge 2025 - Équipe Patria*
