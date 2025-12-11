# 📋 Spécifications Techniques - Agent IA Sonalyze

**Projet :** Agent d'interprétation Sonalyze  
**Client :** Sonalyze (Diagnostic Performance Sonore)  
**Équipe :** Patria  
**Date :** Décembre 2025  
**Version :** 1.0

---

## 1. Contexte et Objectifs

### 1.1 Problématique

Sonalyze propose un diagnostic acoustique low-cost (200€) via un boîtier IoT. Le système génère des **données brutes** (JSON) et des **graphiques**, mais il manque :

- ❌ **Interprétation** : Expliquer la note A-G de manière pédagogique
- ❌ **Recommandations** : Proposer des solutions concrètes et chiffrées

### 1.2 Solution

Développer un **Agent IA** capable de :

1. ✅ Interpréter les données JSON du capteur
2. ✅ Générer des explications compréhensibles
3. ✅ Proposer des recommandations personnalisées
4. ✅ Produire un rapport PDF style DPE

### 1.3 Proposition de valeur

| Avant (Sonalyze seul) | Après (+ Agent IA Patria) |
|----------------------|---------------------------|
| Données brutes | Données interprétées |
| Graphiques techniques | Graphiques lisibles avec notes |
| Note A-G sans contexte | Explication de la note |
| Pas de conseils | Recommandations par élément |

---

## 2. Spécifications Fonctionnelles

### 2.1 Données d'entrée

#### 2.1.1 Fichier JSON du capteur

| Champ | Type | Description |
|-------|------|-------------|
| `box_id` | string | Identifiant du boîtier |
| `timestamp` | datetime | Date/heure de mesure |
| `LAeq_segment_dB` | float | Niveau sonore équivalent (dB) |
| `LAeq_rating` | string | Note A-G du segment |
| `Lmin_dB` | float | Niveau minimum |
| `Lmax_dB` | float | Niveau maximum |
| `top_5_labels` | array | 5 sons principaux détectés |
| `top_5_probs` | array | Probabilités associées |

#### 2.1.2 Informations logement (saisie utilisateur)

| Champ | Type | Obligatoire |
|-------|------|-------------|
| `type` | enum | Oui (Appartement/Maison) |
| `etage` | int | Non |
| `piece` | enum | Oui (Chambre/Salon/...) |
| `ville` | string | Non |
| `adresse` | string | Non |

### 2.2 Traitements

#### 2.2.1 Validation des données

- Structure JSON conforme
- Timestamps valides (format ISO)
- Valeurs dB dans [0, 130]
- Probabilités dans [0, 1]

#### 2.2.2 Calculs statistiques

| Métrique | Formule | Usage |
|----------|---------|-------|
| Moyenne dB | `mean(LAeq_segment_dB)` | Note globale |
| Séparation jour/nuit | `hour >= 22 OR hour < 7` | Comparaison |
| Top 5 sons | `value_counts()[:5]` | Identification sources |
| Distribution notes | `groupby(LAeq_rating)` | Répartition |

#### 2.2.3 Classification des sons

**527 classes AudioSet → 11 familles**

| Famille | Caractère | Exemples |
|---------|-----------|----------|
| `circulation` | Problématique | Vehicle, Car, Truck |
| `transport` | Problématique | Train, Aircraft |
| `voisinage` | Modéré | Speech, Footsteps |
| `musique` | Modéré | Music, Guitar |
| `nature` | Positif | Bird, Rain |
| `travaux` | Problématique | Drill, Hammer |

#### 2.2.4 Calcul de la note DPS

| Note | Seuil (dB) | Description |
|------|-----------|-------------|
| A | ≤ 20 | Exceptionnel |
| B | ≤ 30 | Très bon |
| C | ≤ 45 | Bon |
| D | ≤ 60 | Moyen |
| E | ≤ 80 | Insuffisant |
| F | ≤ 100 | Très insuffisant |
| G | > 100 | Critique |

### 2.3 Données de sortie

#### 2.3.1 Analyse structurée

```python
{
    "global": {
        "db_mean": float,      # Moyenne dB
        "note_globale": str,   # A-G
        "duration_hours": float
    },
    "day_night": {
        "jour": {"mean": float, "count": int},
        "nuit": {"mean": float, "count": int}
    },
    "sounds": {
        "top_5": [...],        # Top 5 global
        "top_5_jour": [...],   # Top 5 jour
        "top_5_nuit": [...],   # Top 5 nuit
        "families_jour": {...}, # Familles jour
        "families_nuit": {...}  # Familles nuit
    }
}
```

#### 2.3.2 Graphiques

| ID | Type | Description |
|----|------|-------------|
| `gauge` | Jauge | Note globale style DPE |
| `rating_bars` | Barres | Distribution A-G |
| `day_night` | Barres groupées | Comparaison jour/nuit |
| `top_sounds_jour` | Barres H | Top 5 sons jour |
| `top_sounds_nuit` | Barres H | Top 5 sons nuit |
| `family_pie_jour` | Camembert | Familles jour |
| `family_pie_nuit` | Camembert | Familles nuit |
| `sounds_heatmap` | Heatmap | 24h × Sons |

#### 2.3.3 Textes IA

| Contenu | Longueur | Usage |
|---------|----------|-------|
| Interprétation note | 2-3 paragraphes | Explication pédagogique |
| Analyse sources | 2-3 paragraphes | Identification nuisances |
| Recommandations | JSON structuré | Solutions par élément |
| Email synthèse | 1 page | Communication client |

---

## 3. Spécifications Techniques

### 3.1 Stack technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.11+ |
| Data | Pandas | 2.0+ |
| Visualisation | Plotly | 5.0+ |
| LLM | Groq API | Llama 3.3 70B |
| Interface | Streamlit | 1.30+ |
| PDF | ReportLab | 4.0+ |

### 3.2 Architecture

```
┌─────────────────────────────────────────┐
│             Interface (Streamlit)        │
├─────────────────────────────────────────┤
│  config.py │ data_loader.py │ charts.py │
├─────────────────────────────────────────┤
│        aggregator.py │ llm_client.py    │
├─────────────────────────────────────────┤
│          API externe (Groq)             │
└─────────────────────────────────────────┘
```

### 3.3 API LLM

**Endpoint :** `https://api.groq.com/openai/v1/chat/completions`

**Configuration :**
```json
{
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.3,
    "max_tokens": 2000
}
```

### 3.4 Performance

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Chargement JSON (8000 seg.) | < 2s | ~0.5s ✅ |
| Analyse complète | < 5s | ~1s ✅ |
| Graphiques | < 5s | ~2s ✅ |
| Appels LLM | < 10s | ~5s ✅ |
| **Pipeline total** | < 20s | ~8s ✅ |

---

## 4. Contraintes et Limites

### 4.1 Contraintes techniques

- Dépendance API Groq (disponibilité)
- Taille fichier JSON < 50 MB
- Connexion internet requise

### 4.2 Limites fonctionnelles

- Pas de mesure en temps réel
- Pas de géolocalisation des sources
- Recommandations génériques (pas sur-mesure)

### 4.3 Évolutions futures

- [ ] Multi-pièces (plusieurs boîtiers)
- [ ] Base de données artisans partenaires
- [ ] Export vers formats supplémentaires
- [ ] API REST publique

---

## 5. Glossaire

| Terme | Définition |
|-------|------------|
| **DPS** | Diagnostic de Performance Sonore |
| **dB** | Décibel - unité de mesure du son |
| **LAeq** | Niveau sonore équivalent pondéré A |
| **AST** | Audio Spectrogram Transformer (modèle IA) |
| **AudioSet** | Base de données de 527 classes sonores |

---

## 6. Références

- AudioSet : https://research.google.com/audioset/
- AST Paper : https://arxiv.org/abs/2104.01778
- Groq API : https://console.groq.com/docs
- Normes acoustiques : NF S31-080

---

*Document rédigé par l'équipe Patria - Hackathon La Forge 2025*
