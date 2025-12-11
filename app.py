"""
=============================================================================
SONALYZE DASHBOARD - Application Multi-Pages
=============================================================================
Point d'entrée principal de l'application.
Structure multi-pages Streamlit avec gestion clients + rapports.

Pages disponibles:
- Gestion Clients : CRM, formulaires, liste clients
- Rapport : Dashboard interactif avec graphiques et interprétations IA

Auteur: Équipe Patria
Date: Décembre 2024
=============================================================================
"""

import streamlit as st
from pathlib import Path

# ============================================================
#                  CONFIGURATION STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Sonalyze Dashboard",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
#                  CHARGEMENT DES STATS
# ============================================================

def get_quick_stats():
    """Récupère les statistiques rapides depuis les fichiers clients."""
    clients_dir = Path(__file__).parent / "data" / "clients"
    
    stats = {
        "total_clients": 0,
        "en_cours": 0,
        "termines": 0,
        "avec_boitier": 0
    }
    
    if clients_dir.exists():
        import json
        for file in clients_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    client = json.load(f)
                    stats["total_clients"] += 1
                    
                    statut = client.get('metadata', {}).get('statut', '')
                    if statut == 'analyse_en_cours':
                        stats["en_cours"] += 1
                    elif statut == 'termine':
                        stats["termines"] += 1
                    
                    if client.get('metadata', {}).get('fichier_json_boitier'):
                        stats["avec_boitier"] += 1
            except:
                pass
    
    return stats


# ============================================================
#                  PAGE D'ACCUEIL
# ============================================================

st.title("Sonalyze Dashboard")
st.markdown("### Le diagnostic de performance sonore intelligent")

st.markdown("---")

# Présentation
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ## Bienvenue
    
    Cette plateforme vous permet de :
    
    - **Gérer vos clients** : Créer des formulaires, suivre les diagnostics
    - **Visualiser les rapports** : Graphiques interactifs, analyses détaillées
    - **Obtenir des interprétations IA** : Conseils personnalisés comme un acousticien
    - **Exporter en PDF** : Rapports professionnels à envoyer aux clients
    """)

with col2:
    st.markdown("""
    ## Pour commencer
    
    **1. Nouveau client ?**
    
    Allez dans **Gestion Clients** pour créer un formulaire
    
    **2. Formulaire reçu ?**
    
    Glissez-le dans l'application pour créer la fiche client
    
    **3. Voir un rapport ?**
    
    Cliquez sur le bouton **Voir** à côté du client
    """)

st.markdown("---")

# Stats rapides
st.markdown("## Aperçu rapide")

stats = get_quick_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Clients enregistrés", value=stats["total_clients"])
    
with col2:
    st.metric(label="Analyses en cours", value=stats["en_cours"])
    
with col3:
    st.metric(label="Diagnostics terminés", value=stats["termines"])
    
with col4:
    st.metric(label="Avec fichier boîtier", value=stats["avec_boitier"])

st.markdown("---")

# Navigation rapide
st.markdown("## Navigation")

col1, col2 = st.columns(2)

with col1:
    if st.button("Gestion Clients", use_container_width=True, type="primary"):
        st.switch_page("pages/1_🏠_Gestion_Clients.py")
    st.markdown("_Créer, importer et gérer les fiches clients_")

with col2:
    if st.button("Voir un Rapport", use_container_width=True):
        st.switch_page("pages/2_📊_Rapport.py")
    st.markdown("_Visualiser les graphiques et l'analyse IA_")

st.markdown("---")

# Infos projet
with st.expander("À propos de Sonalyze"):
    st.markdown("""
    **Sonalyze** propose un diagnostic de performance sonore accessible à tous.
    
    - **Prix** : 200 € (vs 500-2000 € pour un acousticien traditionnel)
    - **Méthode** : Boîtier d'enregistrement 24h + IA de reconnaissance sonore
    - **Résultat** : Note A-G + rapport détaillé + recommandations personnalisées
    
    Cette plateforme utilise l'intelligence artificielle pour transformer les données 
    brutes du boîtier en conseils concrets et compréhensibles pour les particuliers.
    
    ---
    
    **Équipe Patria** | Hackathon La Forge 2024
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Sonalyze Dashboard | Propulsé par Patria | "
    "Le calme à portée de diagnostic"
    "</div>",
    unsafe_allow_html=True
)
