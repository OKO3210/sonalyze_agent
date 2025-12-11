# 🔊 Sonalyze Agent IA

> **Agent d'interprétation intelligent pour le diagnostic de performance sonore**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.40+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Présentation

**Sonalyze Agent** est une application d'intelligence artificielle qui transforme les données brutes de diagnostic acoustique en **rapports compréhensibles** et **recommandations personnalisées**.

Développé par l'équipe **Patria** dans le cadre du hackathon **La Forge 2024**, cet agent accompagne la startup [Sonalyze](https://sonalyze.fr) dans sa mission de démocratiser le diagnostic phonique.

### Le problème résolu

Sonalyze génère des données acoustiques très détaillées (JSON), mais :
- ❌ Les particuliers ne comprennent pas les données techniques
- ❌ Pas d'interprétation humaine de la note A-G
- ❌ Pas de recommandations personnalisées

### Notre solution

Un **conseiller acoustique virtuel** qui :
- ✅ Explique la note DPS en langage simple
- ✅ Identifie les sources de bruit problématiques
- ✅ Propose des solutions concrètes (low cost → travaux)
- ✅ Génère des rapports professionnels

---

## 📸 Captures d'écran

| Dashboard principal | Analyse jour/nuit |
|:---:|:---:|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Jour/Nuit](docs/screenshots/day_night.png) |

---

## 🚀 Installation

### Prérequis

- Python 3.11+
- Clé API Groq (gratuite) : [console.groq.com/keys](https://console.groq.com/keys)

### Étapes

```bash
# 1. Cloner le projet
git clone https://github.com/patria-team/sonalyze-agent.git
cd sonalyze-agent

# 2. Créer l'environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer la clé API
# Créer un fichier .env à la racine :
echo "GROQ_API_KEY=gsk_votre_clé_ici" > .env

# 5. Lancer l'application
streamlit run app.py
```

L'application sera accessible sur **http://localhost:8501**

---

## 📁 Structure du projet

```
sonalyze_agent/
├── 📄 app.py                    # Page d'accueil Streamlit
├── 📁 pages/
│   ├── 1_🏠_Gestion_Clients.py  # CRM clients + upload JSON
│   └── 2_📊_Rapport.py          # Dashboard + graphiques + IA
├── 📁 src/                      # Modules Python
│   ├── __init__.py              # Exports du package
│   ├── config.py                # Constantes DPS, familles sons
│   ├── data_loader.py           # Chargement/validation JSON
│   ├── aggregator.py            # Calculs statistiques jour/nuit
│   ├── charts.py                # Graphiques Plotly (11 charts)
│   └── llm_client.py            # Interprétation IA (Groq/Llama)
├── 📁 data/
│   ├── clients/                 # Fichiers clients JSON
│   └── dps_analysis_pi3_exemple.json  # Données exemple
├── 📁 templates/
│   └── formulaire_client.json   # Template formulaire
├── 📁 exports/
│   ├── rapports_pdf/            # PDFs générés
│   └── charts_html/             # Graphiques HTML
├── 📁 docs/                     # Documentation technique
│   ├── ARCHITECTURE_TECHNIQUE.md
│   ├── SPECIFICATIONS.md
│   └── WORKFLOW.md
├── 📄 requirements.txt
├── 📄 .env                      # Variables d'environnement (non versionné)
└── 📄 README.md
```

---

## 🔧 Utilisation

### 1. Gestion des clients

1. Aller dans **🏠 Gestion Clients**
2. **Tab 1** : Générer un formulaire vide à envoyer au client
3. **Tab 2** : Importer le formulaire rempli + JSON boîtier
4. **Tab 3** : Voir la liste des clients, associer des fichiers JSON

### 2. Génération du rapport

1. Sélectionner un client (bouton 👁️)
2. Le dashboard affiche :
   - **Note globale** (jauge A-G)
   - **Graphiques jour/nuit** (top 5 sons, familles)
   - **Heatmap** sons × heures
3. Cliquer sur **🧠 Générer l'interprétation IA**
4. L'IA analyse et propose :
   - Interprétation de la note
   - Analyse des sources sonores
   - Recommandations personnalisées
   - Email de synthèse

---

## 🧠 Technologies

| Composant | Technologie |
|-----------|-------------|
| Frontend | Streamlit 1.40+ |
| Graphiques | Plotly Express |
| LLM | Groq API (Llama 3.3 70B) |
| Data | Pandas, NumPy |
| Config | python-dotenv |

### Pourquoi Groq ?

- ⚡ **Rapide** : Inférence ultra-rapide (< 1s)
- 💰 **Gratuit** : 14k tokens/min gratuits
- 🧠 **Puissant** : Llama 3.3 70B

---

## 📊 Fonctionnalités

### Graphiques générés

| # | Graphique | Description |
|---|-----------|-------------|
| 1 | Jauge DPS | Note A-G avec niveau dB |
| 2 | Distribution notes | Barres horizontales colorées |
| 3 | Comparaison jour/nuit | Barres groupées |
| 4 | Top 5 sons (jour) | Avec notes par son |
| 5 | Top 5 sons (nuit) | Avec notes par son |
| 6 | Familles sons (jour) | Camembert avec dB moyen |
| 7 | Familles sons (nuit) | Camembert avec dB moyen |
| 8 | Heatmap sons×heures | Zones nuit surlignées |
| 9 | Heatmap horaire | Niveau dB par heure |
| 10 | Top 5 global | Pour compatibilité |
| 11 | Familles global | Pour compatibilité |

### Interprétation IA

- **Note** : Explication en langage simple
- **Sources** : Identification des bruits problématiques
- **Recommandations** : Solutions par élément (fenêtre, mur, plafond...)
- **Email** : Synthèse prête à envoyer

---

## 🔒 Sécurité

- La clé API est stockée dans `.env` (non versionné)
- Aucune donnée personnelle n'est envoyée à l'extérieur
- Les fichiers clients restent en local

---

## 🤝 Équipe Patria

| Rôle | Membre |
|------|--------|
| Chef de projet | Omar |
| Développeur | - |
| Développeur | - |
| Développeur | - |

**Hackathon La Forge 2024** - Projet client Sonalyze

---

## 📝 Licence

MIT License - Voir [LICENSE](LICENSE)

---

## 🙏 Remerciements

- **Sonalyze** pour le sujet passionnant
- **Groq** pour l'API LLM gratuite et rapide
- **La Forge** pour l'organisation du hackathon

---

<p align="center">
  <b>Patria</b> - "Le calme à portée de diagnostic" 🔊
</p>
