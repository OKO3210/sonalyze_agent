"""
=============================================================================
SONALYZE AGENT - Génération des Graphiques
=============================================================================
Génère tous les graphiques nécessaires au rapport DPS :
- Jauge de performance sonore (note A-G)
- Camembert typologie des bruits
- Heatmap 24h × Catégories
- Barres comparatives jour/nuit
- Distribution des notes

Utilise Plotly pour les graphiques interactifs (Streamlit)
et peut exporter en image pour le PDF.

Auteur: Équipe Patria
Date: Décembre 2024
=============================================================================
"""

from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import local (même dossier src/)
from config import DPS_SCALE, get_note_from_db, is_sound_problematic


# =============================================================================
# JAUGE DE PERFORMANCE
# =============================================================================

def create_dps_gauge(db_mean: float, note: str) -> go.Figure:
    """
    Crée la jauge de performance sonore style DPE.

    Affiche la note (A-G) avec une jauge colorée et le niveau dB.

    Args:
        db_mean: Niveau sonore moyen en dB
        note: Note calculée (A-G)

    Returns:
        Figure Plotly
    """
    # Couleurs de l'échelle DPS
    colors = [
        DPS_SCALE["A"]["color"],
        DPS_SCALE["B"]["color"],
        DPS_SCALE["C"]["color"],
        DPS_SCALE["D"]["color"],
        DPS_SCALE["E"]["color"],
        DPS_SCALE["F"]["color"],
        DPS_SCALE["G"]["color"],
    ]

    # Crée la jauge
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=db_mean,
            number={"suffix": " dB", "font": {"size": 40}},
            title={
                "text": f"Note : {note}",
                "font": {"size": 50, "color": DPS_SCALE[note]["color"]},
            },
            gauge={
                "axis": {"range": [0, 120], "tickwidth": 2},
                "bar": {"color": DPS_SCALE[note]["color"], "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 20], "color": colors[0]},
                    {"range": [20, 30], "color": colors[1]},
                    {"range": [30, 45], "color": colors[2]},
                    {"range": [45, 60], "color": colors[3]},
                    {"range": [60, 80], "color": colors[4]},
                    {"range": [80, 100], "color": colors[5]},
                    {"range": [100, 120], "color": colors[6]},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.8,
                    "value": db_mean,
                },
            },
        )
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=80, b=20),
    )

    return fig


# =============================================================================
# DISTRIBUTION DES NOTES
# =============================================================================

def create_rating_bars(distribution: Dict[str, int]) -> go.Figure:
    """
    Crée un graphique en barres horizontales de la distribution des notes.

    Style similaire au DPE avec les couleurs A-G.

    Args:
        distribution: {"A": 120, "B": 340, ...}

    Returns:
        Figure Plotly
    """
    notes = ["A", "B", "C", "D", "E", "F", "G"]
    values = [distribution.get(n, 0) for n in notes]
    colors = [DPS_SCALE[n]["color"] for n in notes]
    labels = [DPS_SCALE[n]["label"] for n in notes]

    # Calcule les pourcentages
    total = sum(values)
    percentages = [round(v / total * 100, 1) if total > 0 else 0 for v in values]

    fig = go.Figure(
        go.Bar(
            y=notes,
            x=values,
            orientation="h",
            marker_color=colors,
            text=[f"{p}%" for p in percentages],
            textposition="auto",
            hovertemplate=(
                "<b>Note %{y}</b><br>%{x} segments (%{text})<br>"
                "%{customdata}<extra></extra>"
            ),
            customdata=labels,
        )
    )

    fig.update_layout(
        title="Distribution des notes sur 24h",
        xaxis_title="Nombre de segments",
        yaxis_title="Note DPS",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis=dict(categoryorder="array", categoryarray=notes[::-1]),
    )

    return fig


# =============================================================================
# CAMEMBERT DES FAMILLES DE SONS
# =============================================================================

# Couleurs harmonieuses par famille (palette moderne)
FAMILY_COLORS = {
    "circulation": "#E74C3C",    # Rouge corail
    "transport": "#E67E22",      # Orange
    "voisinage": "#3498DB",      # Bleu
    "musique": "#9B59B6",        # Violet
    "interieur": "#1ABC9C",      # Turquoise
    "electromenager": "#F39C12", # Jaune doré
    "nature": "#27AE60",         # Vert
    "travaux": "#E74C3C",        # Rouge
    "alertes": "#C0392B",        # Rouge foncé
    "animaux": "#8E44AD",        # Violet foncé
    "autres": "#95A5A6",         # Gris
}


def create_family_pie(
    families_data: Dict, 
    title: str = "Typologie des bruits détectés", 
    with_notes: bool = False
) -> go.Figure:
    """
    Crée le camembert de répartition par famille de sons.

    Args:
        families_data: Soit {"circulation": 4500, ...} 
                       soit {"circulation": {"count": 450, "percentage": 65, "note": "D"}, ...}
        title: Titre du graphique
        with_notes: Si True, les données contiennent des notes

    Returns:
        Figure Plotly
    """
    # Gestion des données vides
    if not families_data:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title=title, height=350)
        return fig

    # Détermine le type de données
    first_value = list(families_data.values())[0]
    is_dict_format = isinstance(first_value, dict)

    if with_notes and is_dict_format:
        # Format avec notes: {"circulation": {"count": 450, ...}}
        labels = [
            f"{fam} ({data.get('note', '?')})" 
            for fam, data in families_data.items()
        ]
        values = [
            data.get("count", data.get("percentage", 0)) 
            for data in families_data.values()
        ]
        db_values = [data.get("avg_db", 0) for data in families_data.values()]
        colors = [
            FAMILY_COLORS.get(fam, "#95A5A6") 
            for fam in families_data.keys()
        ]
        hover_template = (
            "<b>%{label}</b><br>%{percent}<br>"
            "%{customdata:.1f} dB<extra></extra>"
        )
        customdata = db_values
    else:
        # Format simple: {"circulation": 4500, ...}
        labels = list(families_data.keys())
        values = list(families_data.values())
        colors = [FAMILY_COLORS.get(f, "#95A5A6") for f in families_data.keys()]
        hover_template = (
            "<b>%{label}</b><br>%{value} segments<br>"
            "%{percent}<extra></extra>"
        )
        customdata = None

    # Vérifie qu'il y a des valeurs > 0
    if not any(v > 0 for v in values):
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title=title, height=350)
        return fig

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo="label+percent",
            textposition="inside",
            hole=0.3,
            hovertemplate=hover_template,
            customdata=customdata,
        )
    )

    fig.update_layout(
        title=title,
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_family_pie_day_night(
    families_jour: Dict, 
    families_nuit: Dict
) -> Dict[str, go.Figure]:
    """
    Crée deux camemberts séparés pour jour et nuit avec les notes.

    Returns:
        {"jour": Figure, "nuit": Figure}
    """
    return {
        "jour": create_family_pie(
            families_jour, 
            "☀️ Familles de sons - JOUR (7h-22h)", 
            with_notes=True
        ),
        "nuit": create_family_pie(
            families_nuit, 
            "🌙 Familles de sons - NUIT (22h-7h)", 
            with_notes=True
        )
    }


# =============================================================================
# COMPARAISON JOUR / NUIT
# =============================================================================

def create_day_night_comparison(day_night: Dict) -> go.Figure:
    """
    Crée le graphique comparatif jour/nuit.

    Args:
        day_night: {"jour": {"mean": 51, "min": 35, "max": 77}, "nuit": {...}}

    Returns:
        Figure Plotly
    """
    categories = ["Moyen", "Min", "Max"]
    
    jour_data = day_night.get("jour", {})
    nuit_data = day_night.get("nuit", {})
    
    jour_values = [
        jour_data.get("mean", 0) or 0,
        jour_data.get("min", 0) or 0,
        jour_data.get("max", 0) or 0,
    ]
    nuit_values = [
        nuit_data.get("mean", 0) or 0,
        nuit_data.get("min", 0) or 0,
        nuit_data.get("max", 0) or 0,
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Jour (7h-22h)",
            x=categories,
            y=jour_values,
            marker_color="#FFC107",
            text=[f"{v:.1f} dB" for v in jour_values],
            textposition="auto",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Nuit (22h-7h)",
            x=categories,
            y=nuit_values,
            marker_color="#3F51B5",
            text=[f"{v:.1f} dB" for v in nuit_values],
            textposition="auto",
        )
    )

    fig.update_layout(
        title="Comparaison Jour / Nuit",
        xaxis_title="Statistique",
        yaxis_title="Niveau sonore (dB)",
        barmode="group",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


# =============================================================================
# HEATMAPS
# =============================================================================

def create_hourly_heatmap(hourly_data: List[Dict]) -> go.Figure:
    """
    Crée la heatmap des niveaux sonores par heure.

    Args:
        hourly_data: Liste de dicts avec hour, db_mean, db_max, dominant_sound

    Returns:
        Figure Plotly
    """
    if not hourly_data:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title="Niveau sonore moyen par heure", height=200)
        return fig

    df = pd.DataFrame(hourly_data)

    # Crée une matrice simple (1 ligne, 24 colonnes)
    hours = list(range(24))
    db_values = []

    for h in hours:
        row = df[df["hour"] == h]
        if len(row) > 0:
            db_values.append(row["db_mean"].values[0])
        else:
            db_values.append(0)

    fig = go.Figure(
        go.Heatmap(
            z=[db_values],
            x=hours,
            y=["dB moyen"],
            colorscale=[
                [0, "#00A651"],
                [0.25, "#92D050"],
                [0.4, "#FFFF00"],
                [0.55, "#FFC000"],
                [0.7, "#FF6600"],
                [0.85, "#FF0000"],
                [1, "#C00000"],
            ],
            zmin=20,
            zmax=80,
            text=[[f"{v:.0f}" for v in db_values]],
            texttemplate="%{text}",
            hovertemplate="Heure: %{x}h<br>Niveau: %{z:.1f} dB<extra></extra>",
        )
    )

    fig.update_layout(
        title="Niveau sonore moyen par heure",
        xaxis_title="Heure de la journée",
        xaxis=dict(tickmode="linear", tick0=0, dtick=2),
        height=200,
        margin=dict(l=20, r=20, t=50, b=40),
    )

    return fig


def create_sounds_heatmap(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Crée la heatmap complète : Sons × Heures avec note moyenne par son.

    Args:
        df: DataFrame avec les données
        top_n: Nombre de sons à afficher (défaut: 10)

    Returns:
        Figure Plotly
    """
    if df is None or len(df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title="Répartition des sons sur 24h", height=450)
        return fig

    # Récupère les top N sons
    top_sounds = df["top_label"].value_counts().head(top_n).index.tolist()

    # Filtre
    df_filtered = df[df["top_label"].isin(top_sounds)].copy()

    # Calcule la note moyenne par son
    sound_stats = df_filtered.groupby("top_label")["LAeq_segment_dB"].mean()
    sound_notes = {label: get_note_from_db(db) for label, db in sound_stats.items()}

    # Pivot pour la heatmap
    pivot = pd.pivot_table(
        df_filtered,
        values="LAeq_segment_dB",
        index="top_label",
        columns="hour",
        aggfunc="count",
        fill_value=0,
    )

    # Trie par total
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=True)
    pivot = pivot.drop("total", axis=1)

    # Labels avec notes et indicateur problématique
    y_labels = []
    for label in pivot.index:
        note = sound_notes.get(label, "?")
        indicator = "🔴" if is_sound_problematic(label) else ""
        y_labels.append(f"{indicator} {label} ({note})")

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=[f"{h}h" for h in pivot.columns],
            y=y_labels,
            colorscale=[
                [0, "#E8F5E9"],
                [0.3, "#FFF9C4"],
                [0.6, "#FFCC80"],
                [1, "#EF5350"]
            ],
            hovertemplate=(
                "<b>%{y}</b><br>Heure: %{x}<br>"
                "Occurrences: %{z}<extra></extra>"
            ),
        )
    )

    # Zones nuit
    fig.add_vrect(
        x0=-0.5, x1=6.5,
        fillcolor="rgba(63, 81, 181, 0.15)",
        line_width=0,
        annotation_text="🌙 Nuit",
        annotation_position="top left"
    )
    fig.add_vrect(
        x0=21.5, x1=23.5,
        fillcolor="rgba(63, 81, 181, 0.15)",
        line_width=0,
        annotation_text="🌙 Nuit",
        annotation_position="top right"
    )

    fig.update_layout(
        title=f"Répartition des {top_n} sons sur 24h (🔴 = problématique)",
        xaxis_title="Heure",
        yaxis_title="",
        height=450,
        margin=dict(l=200, r=20, t=50, b=40),
    )

    return fig


# =============================================================================
# TOP SONS (BARRES)
# =============================================================================

def create_top_sounds_bar(
    top_sounds: List[Dict], 
    top_n: int = 5, 
    title: str = "Top 5 sons détectés"
) -> go.Figure:
    """
    Crée le graphique en barres des sons les plus fréquents avec leur note DPS.

    Args:
        top_sounds: Liste de dicts avec label, percentage, family, 
                    is_problematic, avg_db, note
        top_n: Nombre de sons à afficher
        title: Titre du graphique

    Returns:
        Figure Plotly
    """
    # Gestion des données vides
    if not top_sounds:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(title=title, height=300)
        return fig

    sounds = top_sounds[:top_n]

    labels = [f"{s['label']} ({s.get('note', '?')})" for s in sounds]
    values = [s["percentage"] for s in sounds]
    db_values = [s.get("avg_db", 0) for s in sounds]
    notes = [s.get("note", "?") for s in sounds]
    
    # Couleur selon la note
    note_colors = {
        "A": "#00A651", "B": "#92D050", "C": "#FFFF00", 
        "D": "#FFC000", "E": "#FF6600", "F": "#FF0000", "G": "#C00000"
    }
    colors = [note_colors.get(n, "#90A4AE") for n in notes]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v}% | {db:.0f}dB" for v, db in zip(values, db_values)],
            textposition="auto",
            hovertemplate=(
                "<b>%{y}</b><br>%{x}% du temps<br>"
                "Note: %{customdata}<extra></extra>"
            ),
            customdata=notes,
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Pourcentage du temps",
        yaxis_title="",
        height=300,
        margin=dict(l=180, r=20, t=50, b=40),
        yaxis=dict(categoryorder="total ascending"),
    )

    return fig


def create_top_sounds_day_night(
    sounds_jour: List[Dict], 
    sounds_nuit: List[Dict]
) -> Dict[str, go.Figure]:
    """
    Crée deux graphiques séparés pour jour et nuit.

    Returns:
        {"jour": Figure, "nuit": Figure}
    """
    return {
        "jour": create_top_sounds_bar(
            sounds_jour, 5, 
            "☀️ Top 5 Sons - JOUR (7h-22h)"
        ),
        "nuit": create_top_sounds_bar(
            sounds_nuit, 5, 
            "🌙 Top 5 Sons - NUIT (22h-7h)"
        )
    }


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def generate_all_charts(analysis: Dict, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère tous les graphiques en un seul appel.

    Args:
        analysis: Résultat de generate_full_analysis()
        df: DataFrame original (pour la heatmap)

    Returns:
        Dictionnaire avec tous les graphiques Plotly
        Les clés *_jour et *_nuit contiennent les versions jour/nuit
    """
    sounds_data = analysis.get("sounds", {})
    
    # Graphiques jour/nuit
    top_sounds_day_night = create_top_sounds_day_night(
        sounds_data.get("top_5_jour", []),
        sounds_data.get("top_5_nuit", [])
    )
    family_pie_day_night = create_family_pie_day_night(
        sounds_data.get("families_jour", {}),
        sounds_data.get("families_nuit", {})
    )
    
    global_stats = analysis.get("global", {})
    
    return {
        # Graphique principal
        "gauge": create_dps_gauge(
            global_stats.get("db_mean", 45), 
            global_stats.get("note_globale", "D")
        ),
        # Distribution des notes
        "rating_bars": create_rating_bars(
            analysis.get("ratings", {}).get("distribution", {})
        ),
        # Comparaison jour/nuit
        "day_night": create_day_night_comparison(
            analysis.get("day_night", {})
        ),
        # Heatmap avec notes
        "sounds_heatmap": create_sounds_heatmap(df, top_n=10),
        # Heatmap horaire
        "hourly_heatmap": create_hourly_heatmap(
            analysis.get("hourly", [])
        ),
        
        # === GRAPHIQUES JOUR/NUIT ===
        "top_sounds_jour": top_sounds_day_night["jour"],
        "top_sounds_nuit": top_sounds_day_night["nuit"],
        "family_pie_jour": family_pie_day_night["jour"],
        "family_pie_nuit": family_pie_day_night["nuit"],
        
        # === GRAPHIQUES GLOBAUX (pour compatibilité) ===
        "top_sounds": create_top_sounds_bar(
            sounds_data.get("top_5", []), 
            5, 
            "Top 5 sons détectés (global)"
        ),
        "family_pie": create_family_pie(
            sounds_data.get("families", {})
        ),
    }


# =============================================================================
# TEST DU MODULE
# =============================================================================

if __name__ == "__main__":
    import os
    from pathlib import Path
    
    from data_loader import DataLoader
    from aggregator import generate_full_analysis

    print("\n" + "=" * 60)
    print("TEST CHARTS")
    print("=" * 60 + "\n")

    # Chemin relatif depuis src/
    data_path = Path(__file__).parent.parent / "data" / "dps_analysis_pi3_exemple.json"
    exports_path = Path(__file__).parent.parent / "exports" / "charts_html"
    
    # Crée le dossier exports si nécessaire
    exports_path.mkdir(parents=True, exist_ok=True)

    # Charge les données
    loader = DataLoader(str(data_path))
    df = loader.load()

    # Génère l'analyse
    analysis = generate_full_analysis(df)

    # Génère tous les graphiques
    charts = generate_all_charts(analysis, df)

    print(f"✅ {len(charts)} graphiques générés :")
    for name in charts.keys():
        print(f"   - {name}")

    # Sauvegarde en HTML
    print("\n📊 Sauvegarde des graphiques en HTML...")

    for name, fig in charts.items():
        filepath = exports_path / f"chart_{name}.html"
        fig.write_html(str(filepath))
        print(f"   ✅ {filepath}")

    print("\n🎉 Ouvre les fichiers HTML dans ton navigateur !")
