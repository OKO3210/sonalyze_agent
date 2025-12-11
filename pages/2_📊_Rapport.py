"""
=============================================================================
RAPPORT CLIENT - Dashboard Sonalyze
=============================================================================
Page de visualisation du rapport complet :
- Infos client en header
- Graphiques interactifs (jour/nuit séparés)
- Interprétations IA via Groq
- Recommandations personnalisées avec coûts
- Récapitulatif budgétaire interactif
- Génération PDF professionnel

Auteur: Équipe Patria
Date: Décembre 2024
=============================================================================
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

# ============================================================
#                  CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
EXPORTS_DIR = BASE_DIR / "exports" / "rapports_pdf"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ============================================================
#                  IMPORTS MODULES
# ============================================================

MODULES_AVAILABLE = False
PDF_AVAILABLE = False
IMPORT_ERROR = ""

try:
    from data_loader import DataLoader
    from aggregator import generate_full_analysis
    from charts import generate_all_charts
    from llm_client import generate_all_interpretations, calculate_total_costs
    
    MODULES_AVAILABLE = True
except ImportError as e:
    IMPORT_ERROR = str(e)

try:
    from pdf_generator import generate_pdf_report, check_reportlab_available
    PDF_AVAILABLE = check_reportlab_available()
except ImportError:
    PDF_AVAILABLE = False


# ============================================================
#                  FONCTIONS UTILITAIRES
# ============================================================

def load_json_from_upload(uploaded_file):
    """
    Charge un fichier JSON uploadé et retourne un DataFrame.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.json',
            mode='wb'
        ) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        loader = DataLoader(tmp_path)
        df = loader.load()
        
        return df, None
        
    except Exception as e:
        return None, str(e)
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def get_logement_info_from_client(client_data):
    """
    Extrait les infos logement du client pour le LLM.
    """
    if not client_data:
        return {
            "type": "Appartement",
            "etage": "Non précisé",
            "piece": "Salon",
            "ville": "Non précisée",
            "nom": "Client",
            "adresse": "Non précisée"
        }
    
    info_client = client_data.get('informations_client', {})
    info_logement = client_data.get('informations_logement', {})
    
    return {
        "type": info_logement.get('type_logement', 'Appartement'),
        "etage": info_logement.get('etage', 'Non précisé'),
        "piece": "Salon",
        "ville": info_logement.get('ville', 'Non précisée'),
        "nom": f"{info_client.get('nom', '')} {info_client.get('prenom', '')}".strip() or "Client",
        "adresse": info_logement.get('adresse', 'Non précisée')
    }


def format_price(value):
    """Formate un prix avec séparateur de milliers."""
    return f"{value:,}".replace(",", " ")


def prepare_analysis_for_pdf(analysis: dict) -> dict:
    """
    Prépare les données d'analyse pour le PDF avec toutes les données jour/nuit.
    """
    global_stats = analysis.get('global', {})
    sons = analysis.get('top_sounds', [])
    
    # Données jour
    day_stats = analysis.get('day', {})
    sons_jour = day_stats.get('top_sounds', sons)  # Fallback sur global
    familles_jour = day_stats.get('families', {})
    
    # Données nuit
    night_stats = analysis.get('night', {})
    sons_nuit = night_stats.get('top_sounds', sons)  # Fallback sur global
    familles_nuit = night_stats.get('families', {})
    
    # Familles globales si pas de données jour/nuit
    familles_global = analysis.get('families', {})
    if not familles_jour:
        familles_jour = familles_global
    if not familles_nuit:
        familles_nuit = familles_global
    
    return {
        'note': global_stats.get('grade', 'C'),
        'niveaux_sonores': {
            'db_avg_day': global_stats.get('db_day_avg', global_stats.get('db_mean', 45)),
            'db_avg_night': global_stats.get('db_night_avg', global_stats.get('db_mean', 35)),
            'db_min': global_stats.get('db_min', 25),
            'db_max': global_stats.get('db_max', 65),
        },
        'sons_detectes': [
            {
                'label': s.get('label', ''),
                'probability': s.get('probability', 0),
                'frequency': s.get('frequency', 'N/A')
            }
            for s in sons[:10]
        ],
        # Données JOUR
        'sons_jour': [
            {
                'label': s.get('label', ''),
                'probability': s.get('probability', 0),
                'frequency': s.get('frequency', 'N/A')
            }
            for s in sons_jour[:8]
        ],
        'familles_jour': familles_jour,
        # Données NUIT
        'sons_nuit': [
            {
                'label': s.get('label', ''),
                'probability': s.get('probability', 0),
                'frequency': s.get('frequency', 'N/A')
            }
            for s in sons_nuit[:8]
        ],
        'familles_nuit': familles_nuit,
        # Données globales
        'familles_global': familles_global,
    }


def prepare_interpretation_for_pdf(interpretation: dict) -> dict:
    """
    Prépare l'interprétation IA pour le PDF.
    """
    # Extraire l'interprétation textuelle
    grade_interpretation = interpretation.get('grade_interpretation', '')
    sounds_analysis = interpretation.get('sounds_analysis', '')
    
    # Extraire les recommandations
    recos = interpretation.get('recommendations', {})
    
    # Extraire les faiblesses depuis l'analyse des sons
    faiblesses = []
    if "faible" in sounds_analysis.lower() or "problème" in sounds_analysis.lower():
        for line in sounds_analysis.split('\n'):
            if any(word in line.lower() for word in ['attention', 'problème', 'faiblesse', 'améliorer']):
                faiblesses.append(line.strip('- ').strip())
    
    return {
        'interpretation': grade_interpretation,
        'classification_bruits': {},  # Simplifier pour le PDF
        'faiblesses': faiblesses[:5],  # Max 5
        'recommandations': recos
    }


# ============================================================
#                  PAGE PRINCIPALE
# ============================================================

st.title("Rapport de Diagnostic Sonore")

current_client = st.session_state.get('current_client', None)

# ============================================================
#                  HEADER CLIENT
# ============================================================

if current_client:
    info_client = current_client.get('informations_client', {})
    info_logement = current_client.get('informations_logement', {})
    metadata = current_client.get('metadata', {})
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Client")
        nom_complet = f"{info_client.get('nom', 'N/A')} {info_client.get('prenom', '')}"
        st.markdown(f"**{nom_complet}**")
        st.markdown(f"Email : {info_client.get('email', 'N/A')}")
        st.markdown(f"Tél : {info_client.get('telephone', 'N/A')}")
    
    with col2:
        st.markdown("### Logement")
        st.markdown(f"**{info_logement.get('adresse', 'N/A')}**")
        ville = f"{info_logement.get('code_postal', '')} {info_logement.get('ville', 'N/A')}"
        st.markdown(f"{ville}")
        type_info = f"{info_logement.get('type_logement', 'N/A')} - {info_logement.get('typologie', '')}"
        st.markdown(f"{type_info}")
        if info_logement.get('etage'):
            st.markdown(f"Étage {info_logement.get('etage')}")
    
    with col3:
        st.markdown("### Environnement")
        env = current_client.get('environnement_exterieur', {})
        st.markdown(f"Circulation routière : **{env.get('bruit_circulation_routiere', 0)}/5**")
        st.markdown(f"Ferroviaire : **{env.get('bruit_ferroviaire', 0)}/5**")
        st.markdown(f"Aérien : **{env.get('bruit_aerien', 0)}/5**")
        if env.get('zones_festives_proximite'):
            dist = env.get('distance_boites_nuit_m')
            st.markdown(f"Zones festives{f' ({dist}m)' if dist else ''}")
    
    st.markdown("---")
    
    fichier_boitier = metadata.get('fichier_json_boitier', '')
    if fichier_boitier:
        boitier_path = DATA_DIR / fichier_boitier
        if boitier_path.exists():
            st.success(f"Fichier boîtier associé : **{fichier_boitier}**")
        else:
            st.warning(f"Fichier boîtier introuvable : {fichier_boitier}")
            fichier_boitier = ''
    else:
        st.warning("Aucun fichier JSON boîtier associé à ce client.")

else:
    st.info("Aucun client sélectionné. Retournez à la gestion des clients.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Gestion clients", use_container_width=True, type="primary"):
            st.switch_page("pages/1_🏠_Gestion_Clients.py")
    with col2:
        if st.button("Accueil", use_container_width=True):
            st.switch_page("app.py")
    
    st.markdown("---")
    st.markdown("### Mode démo")
    st.markdown("Vous pouvez charger un fichier JSON pour tester le rapport.")
    fichier_boitier = ''


# ============================================================
#                  CHARGEMENT DES DONNÉES
# ============================================================

st.header("Données du diagnostic")

json_source = None
df = None

if current_client:
    fichier_boitier = current_client.get('metadata', {}).get('fichier_json_boitier', '')
    if fichier_boitier:
        boitier_path = DATA_DIR / fichier_boitier
        if boitier_path.exists():
            json_source = str(boitier_path)
            st.info(f"Utilisation du fichier client : **{fichier_boitier}**")

uploaded_json = st.file_uploader(
    "Ou charger un autre fichier JSON",
    type=['json'],
    help="Le fichier JSON généré par le boîtier Sonalyze"
)

if uploaded_json:
    json_source = "upload"
    st.success(f"Fichier uploadé : {uploaded_json.name}")

demo_file = DATA_DIR / "dps_analysis_pi3_exemple.json"
if not json_source and demo_file.exists():
    json_source = str(demo_file)
    st.info(f"Utilisation du fichier démo : **{demo_file.name}**")


# ============================================================
#                  ANALYSE ET GRAPHIQUES
# ============================================================

if json_source and MODULES_AVAILABLE:
    
    try:
        with st.spinner("Chargement des données..."):
            if json_source == "upload":
                df, error = load_json_from_upload(uploaded_json)
                if error:
                    st.error(f"Erreur : {error}")
                    st.stop()
            else:
                loader = DataLoader(json_source)
                df = loader.load()
        
        st.success(f"**{len(df):,}** enregistrements chargés")
        
        with st.expander("Aperçu des données brutes"):
            cols_display = ['timestamp', 'LAeq_segment_dB', 'LAeq_rating', 'top_label', 'top_prob']
            st.dataframe(df[cols_display].head(20))
        
        st.markdown("---")
        
        # ========== ANALYSE ==========
        st.header("Analyse et Graphiques")
        
        with st.spinner("Analyse en cours..."):
            analysis = generate_full_analysis(df)
        
        # Stocker l'analyse dans la session
        st.session_state['current_analysis'] = analysis
        
        with st.spinner("Génération des graphiques..."):
            charts = generate_all_charts(analysis, df)
        
        st.success(f"Analyse terminée - {len(charts)} graphiques générés")
        
        # ========== NOTE GLOBALE ==========
        st.markdown("### Note globale")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if 'gauge' in charts:
                st.plotly_chart(charts['gauge'], use_container_width=True)
        
        with col2:
            global_stats = analysis.get('global', {})
            st.metric("Moyenne", f"{global_stats.get('db_mean', 0):.1f} dB")
            st.metric("Minimum", f"{global_stats.get('db_min', 0):.1f} dB")
        
        with col3:
            st.metric("Maximum", f"{global_stats.get('db_max', 0):.1f} dB")
            st.metric("Durée", f"{global_stats.get('duration_hours', 0):.1f}h")
        
        # ========== JOUR / NUIT ==========
        st.markdown("### Analyse Jour / Nuit")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Jour (7h-22h)")
            if 'top_sounds_jour' in charts:
                st.plotly_chart(charts['top_sounds_jour'], use_container_width=True)
            if 'family_pie_jour' in charts:
                st.plotly_chart(charts['family_pie_jour'], use_container_width=True)
        
        with col2:
            st.markdown("#### Nuit (22h-7h)")
            if 'top_sounds_nuit' in charts:
                st.plotly_chart(charts['top_sounds_nuit'], use_container_width=True)
            if 'family_pie_nuit' in charts:
                st.plotly_chart(charts['family_pie_nuit'], use_container_width=True)
        
        # ========== GRAPHIQUES DÉTAILLÉS ==========
        st.markdown("### Graphiques détaillés")
        
        detail_charts = {
            'day_night': 'Comparaison Jour/Nuit',
            'rating_bars': 'Distribution des Notes',
            'sounds_heatmap': 'Heatmap Sons × Heures',
            'hourly_heatmap': 'Niveaux par Heure',
            'top_sounds': 'Top 5 Sons (Global)',
            'family_pie': 'Familles de Sons (Global)'
        }
        
        for chart_key, chart_title in detail_charts.items():
            if chart_key in charts:
                with st.expander(f"{chart_title}"):
                    st.plotly_chart(charts[chart_key], use_container_width=True)
        
        st.markdown("---")
        
        # ========== INTERPRÉTATION IA ==========
        st.header("Interprétation IA")
        
        logement_info = get_logement_info_from_client(current_client)
        
        if st.button("Générer l'interprétation IA", type="primary", use_container_width=True):
            with st.spinner("L'IA analyse vos données... (30-60 sec)"):
                try:
                    interpretation = generate_all_interpretations(analysis, logement_info)
                    st.session_state['interpretation'] = interpretation
                    st.success("Interprétation générée !")
                except Exception as e:
                    st.error(f"Erreur LLM : {e}")
                    st.info("Vérifiez que GROQ_API_KEY est configurée dans .env")
        
        # Afficher l'interprétation si disponible
        if 'interpretation' in st.session_state:
            interpretation = st.session_state['interpretation']
            
            # Note
            with st.expander("Interprétation de la note", expanded=True):
                st.markdown(interpretation.get("grade_interpretation", "_Aucune interprétation_"))
            
            # Sources sonores
            with st.expander("Analyse des sources sonores", expanded=True):
                st.markdown(interpretation.get("sounds_analysis", "_Aucune analyse_"))
            
            # ========== RECOMMANDATIONS ==========
            with st.expander("Recommandations personnalisées", expanded=True):
                recos = interpretation.get("recommendations", {})
                
                # Initialiser les solutions sélectionnées
                if 'selected_solutions' not in st.session_state:
                    st.session_state['selected_solutions'] = {}
                
                for section, contenu in recos.items():
                    if isinstance(contenu, dict) and contenu:
                        priorite = contenu.get('priorite', 'N/A')
                        priorite_colors = {
                            'haute': '#e74c3c', 
                            'moyenne': '#f39c12', 
                            'basse': '#27ae60'
                        }
                        color = priorite_colors.get(priorite, '#95a5a6')
                        
                        st.markdown(f"#### {section.replace('_', ' ').title()}")
                        st.markdown(f"<span style='color:{color}'>Priorité : {priorite}</span>", 
                                   unsafe_allow_html=True)
                        
                        # Points positifs
                        points_positifs = contenu.get('points_positifs', '')
                        if points_positifs:
                            st.markdown(f"**Ce qui est bien :** {points_positifs}")
                        
                        # Problème
                        probleme = contenu.get('probleme', '')
                        if probleme and probleme != "Aucun problème majeur détecté":
                            st.markdown(f"**Point d'attention :** {probleme}")
                        
                        # Solutions
                        solutions = contenu.get("solutions", [])
                        if solutions:
                            st.markdown("**Solutions proposées :**")
                            for i, sol in enumerate(solutions):
                                if isinstance(sol, dict) and sol:
                                    nom = sol.get('nom', 'Solution')
                                    desc = sol.get('description', '')
                                    cout_min = sol.get('cout_min', 0) or 0
                                    cout_max = sol.get('cout_max', 0) or 0
                                    impact = sol.get('impact', '?')
                                    diff = sol.get('difficulte', '?')
                                    
                                    # Affichage de la solution
                                    if cout_max > 0:
                                        cout_txt = f"{format_price(cout_min)} € - {format_price(cout_max)} €"
                                    else:
                                        cout_txt = "Gratuit / inclus"
                                    
                                    st.markdown(
                                        f"- **{nom}** | Coût : {cout_txt} | "
                                        f"Impact : {impact} | Difficulté : {diff}"
                                    )
                                    if desc:
                                        st.markdown(f"  _{desc}_")
                        
                        st.markdown("---")
            
            # ========== RÉCAPITULATIF DES COÛTS ==========
            st.markdown("### Estimation budgétaire")
            
            # Collecter toutes les solutions avec leurs coûts
            all_solutions = []
            for section, contenu in recos.items():
                if isinstance(contenu, dict):
                    priorite = contenu.get('priorite', 'basse')
                    for i, sol in enumerate(contenu.get("solutions", [])):
                        if isinstance(sol, dict):
                            cout_min = sol.get('cout_min', 0) or 0
                            cout_max = sol.get('cout_max', 0) or 0
                            if cout_max > 0:  # Ignorer les solutions gratuites
                                all_solutions.append({
                                    "section": section,
                                    "nom": sol.get('nom', 'Solution'),
                                    "cout_min": cout_min,
                                    "cout_max": cout_max,
                                    "priorite": priorite,
                                    "key": f"{section}_{i}"
                                })
            
            if all_solutions:
                st.markdown("Sélectionnez les solutions que vous envisagez :")
                
                # Grouper par priorité
                haute = [s for s in all_solutions if s['priorite'] == 'haute']
                moyenne = [s for s in all_solutions if s['priorite'] == 'moyenne']
                basse = [s for s in all_solutions if s['priorite'] == 'basse']
                
                selected_cost_min = 0
                selected_cost_max = 0
                selected_names = []
                
                # Afficher par priorité
                for priority_group, label in [
                    (haute, "Priorité haute"),
                    (moyenne, "Priorité moyenne"),
                    (basse, "Priorité basse")
                ]:
                    if priority_group:
                        st.markdown(f"**{label}**")
                        for sol in priority_group:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                checked = st.checkbox(
                                    f"{sol['section'].title()} - {sol['nom']}",
                                    key=f"check_{sol['key']}",
                                    value=sol['priorite'] == 'haute'
                                )
                            with col2:
                                st.markdown(f"{format_price(sol['cout_min'])} - {format_price(sol['cout_max'])} €")
                            
                            if checked:
                                selected_cost_min += sol['cout_min']
                                selected_cost_max += sol['cout_max']
                                selected_names.append(sol['nom'])
                
                # Afficher le total
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Budget minimum", f"{format_price(selected_cost_min)} €")
                with col2:
                    st.metric("Budget maximum", f"{format_price(selected_cost_max)} €")
                with col3:
                    st.metric("Solutions sélectionnées", len(selected_names))
                
                # Stocker pour l'email et le PDF
                st.session_state['selected_cost_range'] = {
                    "min": selected_cost_min,
                    "max": selected_cost_max
                }
                st.session_state['selected_solution_names'] = selected_names
            
            else:
                st.info("Aucune solution payante proposée.")
            
            st.markdown("---")
            
            # ========== EMAIL DE SYNTHÈSE ==========
            with st.expander("Email de synthèse"):
                cost_range = st.session_state.get('selected_cost_range', 
                                                   interpretation.get('cost_range', {}))
                
                email = interpretation.get("summary_email", "_Aucun email_")
                
                if cost_range.get('max', 0) > 0:
                    cost_line = f"\n\nEstimation budgétaire : entre {format_price(cost_range['min'])} € et {format_price(cost_range['max'])} €."
                    if cost_line not in email and "estimation" not in email.lower():
                        if "Cordialement" in email:
                            email = email.replace(
                                "Cordialement", 
                                f"{cost_line}\n\nCordialement"
                            )
                        else:
                            email += cost_line
                
                st.code(email, language="markdown")
                
                if st.button("Copier l'email", use_container_width=True):
                    st.info("Email copié ! (Utilisez Ctrl+C sur le texte ci-dessus)")
        
        st.markdown("---")
        
        # ========== ACTIONS / GÉNÉRATION PDF ==========
        st.header("Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Bouton de génération PDF
            pdf_disabled = not PDF_AVAILABLE
            pdf_help = "Générer un rapport PDF professionnel" if PDF_AVAILABLE else "Installez reportlab: pip install reportlab"
            
            if st.button("Générer PDF", use_container_width=True, type="primary", 
                        disabled=pdf_disabled, help=pdf_help):
                
                if 'interpretation' not in st.session_state:
                    st.warning("Générez d'abord l'interprétation IA pour un PDF complet.")
                
                with st.spinner("Génération du PDF..."):
                    try:
                        # Préparer les données
                        client_data = current_client if current_client else {
                            "informations_client": {"nom": "Client", "prenom": "Test"},
                            "informations_logement": {"adresse": "Adresse test", "ville": "Paris"},
                            "environnement_exterieur": {}
                        }
                        
                        analysis_pdf = prepare_analysis_for_pdf(analysis)
                        
                        interpretation_pdf = None
                        if 'interpretation' in st.session_state:
                            interpretation_pdf = prepare_interpretation_for_pdf(
                                st.session_state['interpretation']
                            )
                        
                        # Générer le PDF
                        pdf_bytes = generate_pdf_report(
                            client_data=client_data,
                            analysis_data=analysis_pdf,
                            interpretation_data=interpretation_pdf
                        )
                        
                        # Créer le nom du fichier
                        nom_client = client_data.get('informations_client', {}).get('nom', 'client')
                        date_str = datetime.now().strftime("%Y%m%d_%H%M")
                        pdf_filename = f"diagnostic_sonalyze_{nom_client}_{date_str}.pdf"
                        
                        # Sauvegarder dans exports/
                        pdf_path = EXPORTS_DIR / pdf_filename
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_bytes)
                        
                        st.success(f"PDF généré : {pdf_filename}")
                        
                        # Bouton de téléchargement
                        st.download_button(
                            label="Télécharger le PDF",
                            data=pdf_bytes,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"Erreur lors de la génération PDF : {e}")
                        with st.expander("Détails de l'erreur"):
                            st.exception(e)
            
            if not PDF_AVAILABLE:
                st.caption("pip install reportlab")
        
        with col2:
            if st.button("Export D3.js", use_container_width=True):
                st.info("Bientôt disponible")
        
        with col3:
            if st.button("Retour clients", use_container_width=True):
                st.switch_page("pages/1_🏠_Gestion_Clients.py")
        
        # Liste des PDFs générés
        pdf_files = list(EXPORTS_DIR.glob("*.pdf"))
        if pdf_files:
            with st.expander(f"PDFs générés ({len(pdf_files)})"):
                for pdf in sorted(pdf_files, reverse=True)[:10]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{pdf.name}**")
                    with col2:
                        with open(pdf, 'rb') as f:
                            st.download_button(
                                "Télécharger",
                                data=f.read(),
                                file_name=pdf.name,
                                mime="application/pdf",
                                key=f"dl_{pdf.name}"
                            )
    
    except Exception as e:
        st.error(f"Erreur lors de l'analyse : {e}")
        with st.expander("Détails de l'erreur"):
            st.exception(e)

elif not MODULES_AVAILABLE:
    st.error(f"Modules non disponibles : {IMPORT_ERROR}")
    st.markdown("""
    ### Configuration requise
    
    Vérifiez que le dossier `src/` contient :
    - `data_loader.py`
    - `aggregator.py`
    - `charts.py`
    - `llm_client.py`
    
    Et installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
    """)

else:
    st.warning("Veuillez charger un fichier JSON pour commencer l'analyse.")


# ============================================================
#                  SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## Options")
    
    show_raw = st.checkbox("Afficher données brutes", value=False)
    
    st.markdown("---")
    
    st.markdown("### Infos rapport")
    if current_client:
        info = current_client.get('informations_client', {})
        st.markdown(f"**Client:** {info.get('nom', 'N/A')}")
        
        meta = current_client.get('metadata', {})
        statut = meta.get('statut', 'N/A')
        st.markdown(f"**Statut:** {statut}")
        
        date = meta.get('date_creation', '')
        if date:
            st.markdown(f"**Créé:** {date[:10]}")
        
        boitier = meta.get('fichier_json_boitier', '')
        if boitier:
            st.markdown(f"**Boîtier:** {boitier}")
    else:
        st.markdown("_Mode démo_")
    
    st.markdown("---")
    
    # Statut PDF
    st.markdown("### Statut modules")
    st.markdown(f"Analyse : {'✅' if MODULES_AVAILABLE else '❌'}")
    st.markdown(f"PDF : {'✅' if PDF_AVAILABLE else '❌'}")
    
    if not PDF_AVAILABLE:
        st.code("pip install reportlab", language="bash")
    
    st.markdown("---")
    
    st.markdown("### Navigation")
    if st.button("Gestion Clients", use_container_width=True):
        st.switch_page("pages/1_🏠_Gestion_Clients.py")
    
    if st.button("Accueil", use_container_width=True):
        st.switch_page("app.py")
