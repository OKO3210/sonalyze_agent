"""
=============================================================================
GESTION CLIENTS - CRM Sonalyze
=============================================================================
Page de gestion des clients :
- Génération de formulaires HTML interactifs à envoyer aux clients
- Import des formulaires JSON remplis par les clients
- Liste des clients avec actions
- Association de fichiers JSON boîtier aux clients existants

Auteur: Équipe Patria
Date: Décembre 2024
=============================================================================
"""

import copy
import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

# ============================================================
#                  CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).parent.parent
CLIENTS_DIR = BASE_DIR / "data" / "clients"
TEMPLATES_DIR = BASE_DIR / "templates"
EXPORTS_DIR = BASE_DIR / "exports" / "rapports_pdf"
DATA_DIR = BASE_DIR / "data"

CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

TYPES_PIECES = [
    "Chambre", "Salon", "Cuisine", "Salle de bain", "Toilettes",
    "Couloir", "Bureau", "Salle à manger", "Cave", "Garage", "Autre"
]

TYPOLOGIES = ["Studio", "T1", "T2", "T3", "T4", "T5", "T6+"]
TYPES_LOGEMENT = ["Appartement", "Maison"]


# ============================================================
#                  FORMULAIRE HTML TEMPLATE
# ============================================================

FORMULAIRE_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulaire Diagnostic Sonalyze</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .form-content { padding: 30px; }
        .section {
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
        }
        .section-header {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
            font-weight: 600;
            color: #2c3e50;
            font-size: 16px;
        }
        .section-content { padding: 20px; }
        .form-row { display: flex; gap: 20px; margin-bottom: 15px; }
        .form-group { flex: 1; }
        .form-group.full { flex: 100%; }
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            color: #444;
            font-size: 14px;
        }
        label .required { color: #e74c3c; }
        input, select, textarea {
            width: 100%;
            padding: 12px 14px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        input::placeholder { color: #aaa; }
        .slider-group { display: flex; align-items: center; gap: 15px; }
        .slider-group input[type="range"] {
            flex: 1;
            padding: 0;
            height: 8px;
            -webkit-appearance: none;
            background: #e0e0e0;
            border-radius: 4px;
            border: none;
        }
        .slider-group input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            background: #667eea;
            border-radius: 50%;
            cursor: pointer;
        }
        .slider-value {
            min-width: 40px;
            text-align: center;
            font-weight: 600;
            color: #667eea;
        }
        .checkbox-group { display: flex; align-items: center; gap: 10px; }
        .checkbox-group input[type="checkbox"] { width: 20px; height: 20px; cursor: pointer; }
        .pieces-container {
            border: 2px dashed #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-top: 10px;
        }
        .piece-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .piece-item input, .piece-item select { flex: 1; min-width: 120px; }
        .btn-remove {
            background: #e74c3c;
            color: white;
            border: none;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 18px;
        }
        .btn-add {
            background: #27ae60;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            margin-top: 10px;
        }
        .btn-add:hover { background: #219a52; }
        .actions {
            display: flex;
            gap: 15px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
        }
        .btn-primary {
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 16px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            flex: 1;
            background: #95a5a6;
            color: white;
            border: none;
            padding: 16px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
        }
        .btn-secondary:hover { background: #7f8c8d; }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 13px;
        }
        .success-message {
            display: none;
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: center;
        }
        .info-box {
            background: #e8f4fd;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
            color: #2c3e50;
        }
        @media (max-width: 600px) {
            .form-row { flex-direction: column; gap: 15px; }
            .piece-item { flex-direction: column; }
            .actions { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Diagnostic de Performance Sonore</h1>
            <p>Formulaire d'information - Merci de remplir tous les champs</p>
        </div>

        <form id="sonalyzeForm" class="form-content">
            <div class="info-box">
                Ce formulaire nous permet de préparer votre diagnostic sonore. 
                Une fois complété, cliquez sur <strong>"Télécharger mes réponses"</strong> et renvoyez le fichier JSON à votre diagnostiqueur.
            </div>

            <!-- SECTION 1: Informations client -->
            <div class="section">
                <div class="section-header">1. Vos coordonnées</div>
                <div class="section-content">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Nom <span class="required">*</span></label>
                            <input type="text" id="nom" required placeholder="Votre nom">
                        </div>
                        <div class="form-group">
                            <label>Prénom <span class="required">*</span></label>
                            <input type="text" id="prenom" required placeholder="Votre prénom">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Email <span class="required">*</span></label>
                            <input type="email" id="email" required placeholder="votre@email.com">
                        </div>
                        <div class="form-group">
                            <label>Téléphone</label>
                            <input type="tel" id="telephone" placeholder="06 XX XX XX XX">
                        </div>
                    </div>
                </div>
            </div>

            <!-- SECTION 2: Informations logement -->
            <div class="section">
                <div class="section-header">2. Votre logement</div>
                <div class="section-content">
                    <div class="form-row">
                        <div class="form-group full">
                            <label>Nom du logement (optionnel)</label>
                            <input type="text" id="nom_logement" placeholder="Ex: Appartement principal, Maison de campagne...">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group full">
                            <label>Adresse <span class="required">*</span></label>
                            <input type="text" id="adresse" required placeholder="Numéro et nom de rue">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Code postal <span class="required">*</span></label>
                            <input type="text" id="code_postal" required placeholder="75001" maxlength="5">
                        </div>
                        <div class="form-group">
                            <label>Ville <span class="required">*</span></label>
                            <input type="text" id="ville" required placeholder="Paris">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Type de logement <span class="required">*</span></label>
                            <select id="type_logement" required>
                                <option value="">-- Sélectionner --</option>
                                <option value="Appartement">Appartement</option>
                                <option value="Maison">Maison</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Étage (si appartement)</label>
                            <select id="etage">
                                <option value="">-- Sélectionner --</option>
                                <option value="RDC">Rez-de-chaussée</option>
                                <option value="1">1er étage</option>
                                <option value="2">2ème étage</option>
                                <option value="3">3ème étage</option>
                                <option value="4">4ème étage</option>
                                <option value="5">5ème étage</option>
                                <option value="6+">6ème étage ou plus</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Typologie <span class="required">*</span></label>
                            <select id="typologie" required>
                                <option value="">-- Sélectionner --</option>
                                <option value="Studio">Studio</option>
                                <option value="T1">T1</option>
                                <option value="T2">T2</option>
                                <option value="T3">T3</option>
                                <option value="T4">T4</option>
                                <option value="T5">T5</option>
                                <option value="T6+">T6 ou plus</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Surface totale (m²)</label>
                            <input type="number" id="surface_totale" placeholder="Ex: 65" min="1" max="1000">
                        </div>
                    </div>
                </div>
            </div>

            <!-- SECTION 3: Pièces -->
            <div class="section">
                <div class="section-header">3. Les pièces de votre logement</div>
                <div class="section-content">
                    <p style="margin-bottom: 15px; color: #666; font-size: 14px;">
                        Ajoutez chaque pièce où vous souhaitez un diagnostic. Le boîtier sera placé dans la pièce principale.
                    </p>
                    <div id="pieces-container" class="pieces-container"></div>
                    <button type="button" class="btn-add" onclick="addPiece()">+ Ajouter une pièce</button>
                </div>
            </div>

            <!-- SECTION 4: Environnement extérieur -->
            <div class="section">
                <div class="section-header">4. Environnement sonore extérieur</div>
                <div class="section-content">
                    <p style="margin-bottom: 20px; color: #666; font-size: 14px;">
                        Évaluez le niveau de bruit de votre environnement (0 = aucun, 5 = très fort)
                    </p>
                    
                    <div class="form-group" style="margin-bottom: 20px;">
                        <label>Bruit de circulation routière</label>
                        <div class="slider-group">
                            <span>0</span>
                            <input type="range" id="bruit_circulation" min="0" max="5" value="0" 
                                   oninput="document.getElementById('val_circulation').textContent = this.value">
                            <span>5</span>
                            <span class="slider-value" id="val_circulation">0</span>
                        </div>
                    </div>
                    
                    <div class="form-group" style="margin-bottom: 20px;">
                        <label>Bruit ferroviaire (train, métro, tramway)</label>
                        <div class="slider-group">
                            <span>0</span>
                            <input type="range" id="bruit_ferroviaire" min="0" max="5" value="0"
                                   oninput="document.getElementById('val_ferroviaire').textContent = this.value">
                            <span>5</span>
                            <span class="slider-value" id="val_ferroviaire">0</span>
                        </div>
                    </div>
                    
                    <div class="form-group" style="margin-bottom: 20px;">
                        <label>Bruit aérien (avions, hélicoptères)</label>
                        <div class="slider-group">
                            <span>0</span>
                            <input type="range" id="bruit_aerien" min="0" max="5" value="0"
                                   oninput="document.getElementById('val_aerien').textContent = this.value">
                            <span>5</span>
                            <span class="slider-value" id="val_aerien">0</span>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <div class="checkbox-group">
                                <input type="checkbox" id="zones_festives">
                                <label for="zones_festives" style="margin: 0;">Zones festives à proximité (bars, boîtes de nuit)</label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group" id="distance_boites_group" style="display: none; margin-top: 15px;">
                        <label>Distance approximative (en mètres)</label>
                        <input type="number" id="distance_boites" placeholder="Ex: 200" min="0" max="5000">
                    </div>
                </div>
            </div>

            <!-- SECTION 5: Commentaires -->
            <div class="section">
                <div class="section-header">5. Informations complémentaires (optionnel)</div>
                <div class="section-content">
                    <div class="form-group">
                        <label>Décrivez vos nuisances sonores principales</label>
                        <textarea id="commentaires" rows="4" 
                                  placeholder="Ex: Bruit de circulation la nuit, voisins bruyants le week-end, travaux fréquents dans l'immeuble..."></textarea>
                    </div>
                </div>
            </div>

            <!-- Actions -->
            <div class="actions">
                <button type="button" class="btn-secondary" onclick="resetForm()">Effacer tout</button>
                <button type="button" class="btn-primary" onclick="downloadJSON()">Télécharger mes réponses</button>
            </div>

            <div id="success-message" class="success-message">
                Fichier téléchargé avec succès ! Envoyez le fichier JSON à votre diagnostiqueur.
            </div>
        </form>

        <div class="footer">
            Sonalyze - Diagnostic de Performance Sonore<br>
            Le calme à portée de diagnostic
        </div>
    </div>

    <script>
        let pieceCount = 0;
        const typesPieces = ["Chambre", "Salon", "Cuisine", "Salle de bain", "Toilettes",
                             "Couloir", "Bureau", "Salle à manger", "Cave", "Garage", "Autre"];

        window.onload = function() { addPiece(); };

        document.getElementById('zones_festives').addEventListener('change', function() {
            document.getElementById('distance_boites_group').style.display = this.checked ? 'block' : 'none';
        });

        function addPiece() {
            pieceCount++;
            const container = document.getElementById('pieces-container');
            const pieceDiv = document.createElement('div');
            pieceDiv.className = 'piece-item';
            pieceDiv.id = `piece-${pieceCount}`;
            
            let optionsHTML = '<option value="">-- Type --</option>';
            typesPieces.forEach(type => { optionsHTML += `<option value="${type}">${type}</option>`; });
            
            pieceDiv.innerHTML = `
                <input type="text" placeholder="Nom (ex: Chambre parentale)" id="piece_nom_${pieceCount}">
                <select id="piece_type_${pieceCount}">${optionsHTML}</select>
                <input type="number" placeholder="Surface m²" min="1" max="500" id="piece_surface_${pieceCount}" style="max-width: 100px;">
                <button type="button" class="btn-remove" onclick="removePiece(${pieceCount})">×</button>
            `;
            container.appendChild(pieceDiv);
        }

        function removePiece(id) {
            const piece = document.getElementById(`piece-${id}`);
            if (piece) piece.remove();
        }

        function collectPieces() {
            const pieces = [];
            const container = document.getElementById('pieces-container');
            const pieceItems = container.querySelectorAll('.piece-item');
            
            pieceItems.forEach(item => {
                const id = item.id.split('-')[1];
                const nom = document.getElementById(`piece_nom_${id}`)?.value || '';
                const type = document.getElementById(`piece_type_${id}`)?.value || '';
                const surface = document.getElementById(`piece_surface_${id}`)?.value || '';
                
                if (nom || type) {
                    pieces.push({
                        nom: nom || type,
                        type: type,
                        surface_m2: surface ? parseFloat(surface) : null
                    });
                }
            });
            return pieces;
        }

        function collectFormData() {
            const now = new Date().toISOString();
            return {
                informations_client: {
                    nom: document.getElementById('nom').value,
                    prenom: document.getElementById('prenom').value,
                    email: document.getElementById('email').value,
                    telephone: document.getElementById('telephone').value
                },
                informations_logement: {
                    nom_logement: document.getElementById('nom_logement').value,
                    adresse: document.getElementById('adresse').value,
                    code_postal: document.getElementById('code_postal').value,
                    ville: document.getElementById('ville').value,
                    type_logement: document.getElementById('type_logement').value,
                    etage: document.getElementById('etage').value,
                    typologie: document.getElementById('typologie').value,
                    surface_totale_m2: document.getElementById('surface_totale').value 
                        ? parseFloat(document.getElementById('surface_totale').value) : null
                },
                pieces: collectPieces(),
                environnement_exterieur: {
                    bruit_circulation_routiere: parseInt(document.getElementById('bruit_circulation').value),
                    bruit_ferroviaire: parseInt(document.getElementById('bruit_ferroviaire').value),
                    bruit_aerien: parseInt(document.getElementById('bruit_aerien').value),
                    zones_festives_proximite: document.getElementById('zones_festives').checked,
                    distance_boites_nuit_m: document.getElementById('distance_boites').value 
                        ? parseInt(document.getElementById('distance_boites').value) : null
                },
                commentaires: document.getElementById('commentaires').value,
                metadata: {
                    date_creation: now,
                    date_modification: now,
                    statut: "en_attente",
                    fichier_json_boitier: "",
                    source: "formulaire_client"
                }
            };
        }

        function validateForm() {
            const required = ['nom', 'prenom', 'email', 'adresse', 'code_postal', 'ville', 'type_logement', 'typologie'];
            let valid = true;
            
            required.forEach(id => {
                const el = document.getElementById(id);
                if (!el.value) {
                    el.style.borderColor = '#e74c3c';
                    valid = false;
                } else {
                    el.style.borderColor = '#e0e0e0';
                }
            });
            
            if (!valid) alert('Veuillez remplir tous les champs obligatoires (marqués d\\'un *)');
            return valid;
        }

        function downloadJSON() {
            if (!validateForm()) return;
            
            const data = collectFormData();
            const json = JSON.stringify(data, null, 2);
            
            const nom = data.informations_client.nom || 'client';
            const prenom = data.informations_client.prenom || '';
            const date = new Date().toISOString().slice(0,10);
            const filename = `sonalyze_${nom}_${prenom}_${date}.json`.toLowerCase().replace(/\\s+/g, '_');
            
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            document.getElementById('success-message').style.display = 'block';
            setTimeout(() => { document.getElementById('success-message').style.display = 'none'; }, 5000);
        }

        function resetForm() {
            if (confirm('Êtes-vous sûr de vouloir effacer toutes vos réponses ?')) {
                document.getElementById('sonalyzeForm').reset();
                document.getElementById('pieces-container').innerHTML = '';
                document.getElementById('distance_boites_group').style.display = 'none';
                document.getElementById('val_circulation').textContent = '0';
                document.getElementById('val_ferroviaire').textContent = '0';
                document.getElementById('val_aerien').textContent = '0';
                pieceCount = 0;
                addPiece();
            }
        }
    </script>
</body>
</html>'''


# ============================================================
#                  FONCTIONS UTILITAIRES
# ============================================================

def load_clients():
    """Charger tous les clients depuis le dossier data/clients."""
    clients = []
    if CLIENTS_DIR.exists():
        for file in CLIENTS_DIR.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    client = json.load(f)
                    client['_filename'] = file.name
                    client['_filepath'] = str(file)
                    clients.append(client)
            except json.JSONDecodeError as e:
                st.warning(f"Erreur JSON dans {file.name}: {e}")
            except Exception as e:
                st.warning(f"Erreur lecture {file.name}: {e}")
    return clients


def save_client(client_data, filename=None):
    """Sauvegarder un client dans un fichier JSON."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom = client_data.get('informations_client', {}).get('nom', 'client')
        prenom = client_data.get('informations_client', {}).get('prenom', '')
        filename = f"{nom}_{prenom}_{timestamp}.json".replace(" ", "_").lower()
    
    filepath = CLIENTS_DIR / filename
    
    client_to_save = {k: v for k, v in client_data.items() 
                      if not k.startswith('_')}
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(client_to_save, f, ensure_ascii=False, indent=2)
    
    return filename


def update_client_json_boitier(client_filepath, json_boitier_filename):
    """Met à jour le fichier JSON boîtier associé à un client."""
    try:
        with open(client_filepath, 'r', encoding='utf-8') as f:
            client_data = json.load(f)
        
        client_data['metadata']['fichier_json_boitier'] = json_boitier_filename
        client_data['metadata']['date_modification'] = datetime.now().isoformat()
        
        if client_data['metadata'].get('statut') == 'en_attente':
            client_data['metadata']['statut'] = 'analyse_en_cours'
        
        with open(client_filepath, 'w', encoding='utf-8') as f:
            json.dump(client_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour : {e}")
        return False


def parse_uploaded_form(uploaded_file):
    """Parser un formulaire JSON uploadé par le client."""
    try:
        content = uploaded_file.read().decode('utf-8')
        data = json.loads(content)
        
        # Valider la structure minimale
        required_keys = ['informations_client', 'informations_logement']
        for key in required_keys:
            if key not in data:
                return None, f"Structure invalide : clé '{key}' manquante"
        
        # Mettre à jour les métadonnées
        if 'metadata' not in data:
            data['metadata'] = {}
        data['metadata']['date_modification'] = datetime.now().isoformat()
        
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON invalide : {e}"
    except Exception as e:
        return None, str(e)


def get_available_json_boitiers():
    """Liste les fichiers JSON boîtier disponibles dans data/."""
    json_files = []
    if DATA_DIR.exists():
        for file in DATA_DIR.glob("*.json"):
            json_files.append(file.name)
    return sorted(json_files)


# ============================================================
#                  PAGE STREAMLIT
# ============================================================

st.set_page_config(page_title="Gestion Clients - Sonalyze", page_icon="🏠", layout="wide")

st.title("Gestion Clients")
st.markdown("Gérez vos clients, créez des formulaires et suivez les diagnostics.")

tab1, tab2, tab3 = st.tabs([
    "Envoyer Formulaire", 
    "Importer Réponse Client", 
    "Liste Clients"
])

# ============================================================
#                  TAB 1: ENVOYER FORMULAIRE HTML
# ============================================================

with tab1:
    st.markdown("### Générer un formulaire pour votre client")
    
    st.info("""
    **Comment ça marche ?**
    1. Téléchargez le formulaire HTML ci-dessous
    2. Envoyez-le par email à votre client
    3. Le client l'ouvre dans son navigateur, le remplit, et télécharge ses réponses (fichier JSON)
    4. Le client vous renvoie le fichier JSON par email
    5. Vous importez le JSON dans l'onglet "Importer Réponse Client"
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Le formulaire demande au client :**
        - Ses coordonnées (nom, email, téléphone)
        - Les informations du logement (adresse, type, étage)
        - La liste des pièces avec surfaces
        - L'environnement sonore extérieur
        - Ses commentaires sur les nuisances
        """)
    
    with col2:
        st.download_button(
            label="Télécharger le formulaire HTML",
            data=FORMULAIRE_HTML_TEMPLATE,
            file_name="formulaire_sonalyze.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
            help="Fichier HTML à envoyer au client"
        )
    
    with st.expander("Aperçu du formulaire"):
        st.components.v1.html(FORMULAIRE_HTML_TEMPLATE, height=600, scrolling=True)


# ============================================================
#                  TAB 2: IMPORTER RÉPONSE CLIENT
# ============================================================

with tab2:
    st.markdown("### Importer les réponses du client")
    
    # Zone d'upload en haut - BIEN VISIBLE
    uploaded_file = st.file_uploader(
        "Glissez le fichier JSON renvoyé par le client",
        type=['json'],
        help="Le fichier JSON généré par le formulaire",
        key="form_upload"
    )
    
    if uploaded_file is not None:
        data, error = parse_uploaded_form(uploaded_file)
        
        if error:
            st.error(f"Erreur : {error}")
        else:
            st.success("Fichier lu avec succès !")
            
            # BOUTON D'ENREGISTREMENT EN HAUT - TOUJOURS VISIBLE
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.button("ENREGISTRER CE CLIENT", type="primary", use_container_width=True):
                    filename = save_client(data)
                    st.success(f"Client enregistré : {filename}")
                    st.balloons()
                    st.rerun()
            
            st.markdown("---")
            
            # Résumé compact des données
            info_client = data.get('informations_client', {})
            info_logement = data.get('informations_logement', {})
            pieces = data.get('pieces', [])
            environnement = data.get('environnement_exterieur', {})
            
            # Affichage compact en colonnes
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Client**")
                nom_complet = f"{info_client.get('nom', 'N/A')} {info_client.get('prenom', '')}"
                st.write(f"Nom : {nom_complet}")
                st.write(f"Email : {info_client.get('email', 'N/A')}")
            
            with col2:
                st.markdown("**Logement**")
                st.write(f"{info_logement.get('adresse', 'N/A')}")
                st.write(f"{info_logement.get('code_postal', '')} {info_logement.get('ville', '')}")
                st.write(f"{info_logement.get('type_logement', 'N/A')} - {info_logement.get('typologie', '')}")
            
            with col3:
                st.markdown("**Environnement**")
                st.write(f"Circulation : {environnement.get('bruit_circulation_routiere', 0)}/5")
                st.write(f"Ferroviaire : {environnement.get('bruit_ferroviaire', 0)}/5")
                st.write(f"Aérien : {environnement.get('bruit_aerien', 0)}/5")
            
            # Pièces en expander
            if pieces:
                with st.expander(f"Pièces déclarées ({len(pieces)})"):
                    for piece in pieces:
                        surface = piece.get('surface_m2')
                        surface_txt = f" - {surface} m²" if surface else ""
                        st.write(f"• {piece.get('nom', 'N/A')}{surface_txt}")
            
            # Commentaires
            commentaires = data.get('commentaires', '')
            if commentaires:
                with st.expander("Commentaires du client"):
                    st.write(commentaires)
            
            # Option JSON boîtier en expander (pas obligatoire immédiatement)
            with st.expander("Associer le JSON boîtier (optionnel - peut être fait plus tard)"):
                boitier_file = st.file_uploader(
                    "Fichier JSON du boîtier",
                    type=['json'],
                    key="boitier_upload_tab2"
                )
                
                if boitier_file:
                    data['metadata']['fichier_json_boitier'] = boitier_file.name
                    data['metadata']['statut'] = 'analyse_en_cours'
                    st.success(f"Fichier boîtier associé : {boitier_file.name}")
    else:
        st.info("Glissez un fichier JSON pour commencer.")


# ============================================================
#                  TAB 3: LISTE CLIENTS
# ============================================================

with tab3:
    st.markdown("### Liste des clients")
    
    clients = load_clients()
    
    if not clients:
        st.info("Aucun client enregistré. Importez un formulaire pour commencer !")
    else:
        # Barre de recherche et stats
        col_search, col_stats = st.columns([2, 1])
        
        with col_search:
            search = st.text_input(
                "Rechercher", 
                placeholder="Nom, ville, adresse...",
                label_visibility="collapsed"
            )
        
        with col_stats:
            st.markdown(f"**{len(clients)} client(s)**")
        
        if search:
            search_lower = search.lower()
            clients = [c for c in clients if 
                search_lower in c.get('informations_client', {}).get('nom', '').lower() or
                search_lower in c.get('informations_client', {}).get('prenom', '').lower() or
                search_lower in c.get('informations_logement', {}).get('ville', '').lower() or
                search_lower in c.get('informations_logement', {}).get('adresse', '').lower()
            ]
        
        st.markdown("---")
        
        # Liste des clients
        for i, client in enumerate(clients):
            info_client = client.get('informations_client', {})
            info_logement = client.get('informations_logement', {})
            metadata = client.get('metadata', {})
            
            statut = metadata.get('statut', 'en_attente')
            statut_config = {
                'en_attente': ('En attente', '#f39c12'),
                'analyse_en_cours': ('Analyse en cours', '#3498db'), 
                'termine': ('Terminé', '#27ae60')
            }
            statut_label, statut_color = statut_config.get(statut, (statut, '#95a5a6'))
            
            fichier_boitier = metadata.get('fichier_json_boitier', '')
            has_boitier = bool(fichier_boitier)
            
            # Ligne client compacte
            col1, col2, col3, col4 = st.columns([2.5, 3, 1.5, 2.5])
            
            with col1:
                nom_complet = f"{info_client.get('nom', 'N/A')} {info_client.get('prenom', '')}"
                st.markdown(f"**{nom_complet}**")
            
            with col2:
                adresse = info_logement.get('adresse', 'N/A')[:30]
                ville = info_logement.get('ville', '')
                st.markdown(f"{adresse} - {ville}")
            
            with col3:
                st.markdown(f"<span style='color:{statut_color}'>{statut_label}</span>", unsafe_allow_html=True)
            
            with col4:
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button("Voir", key=f"voir_{i}", use_container_width=True):
                        st.session_state['current_client'] = client
                        st.session_state['client_filename'] = client.get('_filename', '')
                        st.switch_page("pages/2_📊_Rapport.py")
                
                with btn_col2:
                    if st.button("PDF", key=f"pdf_{i}", use_container_width=True):
                        st.session_state['current_client'] = client
                        st.session_state['client_filename'] = client.get('_filename', '')
                        st.switch_page("pages/2_📊_Rapport.py")
            
            # Expander pour JSON boîtier
            boitier_status = f"✓ {fichier_boitier}" if has_boitier else "Non associé"
            with st.expander(f"JSON Boîtier : {boitier_status}", expanded=False):
                if not has_boitier:
                    st.warning("Aucun fichier JSON boîtier associé.")
                
                new_boitier = st.file_uploader(
                    "Glisser un fichier JSON boîtier",
                    type=['json'],
                    key=f"boitier_{i}",
                    label_visibility="collapsed"
                )
                
                if new_boitier:
                    try:
                        content = new_boitier.read()
                        json.loads(content.decode('utf-8'))
                        new_boitier.seek(0)
                        
                        boitier_path = DATA_DIR / new_boitier.name
                        with open(boitier_path, 'wb') as f:
                            f.write(content)
                        
                        if update_client_json_boitier(client.get('_filepath'), new_boitier.name):
                            st.success(f"Fichier associé : {new_boitier.name}")
                            st.rerun()
                    except json.JSONDecodeError:
                        st.error("JSON invalide")
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                
                # Sélection fichier existant
                existing_files = get_available_json_boitiers()
                if existing_files:
                    selected = st.selectbox(
                        "Ou sélectionner existant",
                        ["--"] + existing_files,
                        key=f"select_{i}",
                        label_visibility="collapsed"
                    )
                    
                    if selected != "--":
                        if st.button(f"Associer", key=f"assoc_{i}"):
                            if update_client_json_boitier(client.get('_filepath'), selected):
                                st.success(f"Associé : {selected}")
                                st.rerun()
            
            st.markdown("---")


# ============================================================
#                  SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## Statistiques")
    
    clients = load_clients()
    total = len(clients)
    en_attente = len([c for c in clients if c.get('metadata', {}).get('statut') == 'en_attente'])
    en_cours = len([c for c in clients if c.get('metadata', {}).get('statut') == 'analyse_en_cours'])
    termines = len([c for c in clients if c.get('metadata', {}).get('statut') == 'termine'])
    avec_boitier = len([c for c in clients if c.get('metadata', {}).get('fichier_json_boitier')])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", total)
        st.metric("En attente", en_attente)
    with col2:
        st.metric("En cours", en_cours)
        st.metric("Terminés", termines)
    
    st.metric("Avec JSON boîtier", f"{avec_boitier}/{total}")
    
    st.markdown("---")
    st.markdown("### Workflow")
    st.markdown("""
    1. Générer le formulaire HTML
    2. L'envoyer au client par email
    3. Recevoir le JSON rempli
    4. L'importer ici
    5. Ajouter le JSON boîtier
    6. Générer le rapport
    """)
