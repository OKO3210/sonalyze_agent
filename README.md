# sonalyze_agent

# 🔊 Sonalyze Agent

Agent IA d'interprétation pour diagnostics de performance sonore.

## 🎯 Projet

Hackathon La Forge - Client Sonalyze
- **Équipe** : Patria
- **Deadline** : Jeudi 23h

## 📦 Installation
```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
```

## 🚀 Usage
```bash
# Test du chargement de données
python -m src.data_loader data/exemple.json

# Test des statistiques
python -m src.aggregator

# Test des graphiques
python -m src.charts
```

## 📁 Structure
```
src/
├── config.py        # Constantes et seuils DPS
├── data_loader.py   # Chargement JSON
├── aggregator.py    # Calcul statistiques
├── charts.py        # Génération graphiques
├── llm_client.py    # Appels Groq (à venir)
└── app.py           # Interface Streamlit (à venir)
```

## 🛠️ Stack

- Python 3.11+
- Pandas (data processing)
- Plotly (graphiques)
- Streamlit (interface)
- Groq API (LLM)
EOF