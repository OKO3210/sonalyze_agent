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
=============================================================================
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any

from src.config import DPS_SCALE


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
            hovertemplate="<b>Note %{y}</b><br>%{x} segments (%{text})<br>%{customdata}<extra></extra>",
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


def create_family_pie(families: Dict[str, int]) -> go.Figure:
    """
    Crée le camembert de répartition par famille de sons.

    Args:
        families: {"circulation": 4500, "voisinage": 2000, ...}

    Returns:
        Figure Plotly
    """
    # Couleurs par famille
    family_colors = {
        "circulation": "#FF6B6B",
        "transport": "#FF8E72",
        "voisinage": "#4ECDC4",
        "musique": "#45B7D1",
        "interieur": "#96CEB4",
        "electromenager": "#FFEAA7",
        "nature": "#81C784",
        "travaux": "#FFB74D",
        "alertes": "#E57373",
        "animaux": "#BA68C8",
        "autres": "#90A4AE",
    }

    labels = list(families.keys())
    values = list(families.values())
    colors = [family_colors.get(f, "#90A4AE") for f in labels]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo="label+percent",
            textposition="inside",
            hole=0.3,
            hovertemplate="<b>%{label}</b><br>%{value} segments<br>%{percent}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Typologie des bruits détectés",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_day_night_comparison(day_night: Dict) -> go.Figure:
    """
    Crée le graphique comparatif jour/nuit.

    Args:
        day_night: {"jour": {"mean": 51, "min": 35, "max": 77}, "nuit": {...}}

    Returns:
        Figure Plotly
    """
    categories = ["Moyen", "Min", "Max"]
    jour_values = [
        day_night["jour"]["mean"],
        day_night["jour"]["min"],
        day_night["jour"]["max"],
    ]
    nuit_values = [
        day_night["nuit"]["mean"],
        day_night["nuit"]["min"],
        day_night["nuit"]["max"],
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Jour (7h-22h)",
            x=categories,
            y=jour_values,
            marker_color="#FFC107",
            text=[f"{v} dB" for v in jour_values],
            textposition="auto",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Nuit (22h-7h)",
            x=categories,
            y=nuit_values,
            marker_color="#3F51B5",
            text=[f"{v} dB" for v in nuit_values],
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


def create_hourly_heatmap(hourly_data: List[Dict]) -> go.Figure:
    """
    Crée la heatmap des niveaux sonores par heure.

    Args:
        hourly_data: Liste de dicts avec hour, db_mean, db_max, dominant_sound

    Returns:
        Figure Plotly
    """
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


def create_sounds_heatmap(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Crée la heatmap complète : Sons × Heures.

    Args:
        df: DataFrame avec les données
        top_n: Nombre de sons à afficher

    Returns:
        Figure Plotly
    """
    # Récupère les top N sons
    top_sounds = df["top_label"].value_counts().head(top_n).index.tolist()

    # Filtre et pivote
    df_filtered = df[df["top_label"].isin(top_sounds)]

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

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=[f"{h}h" for h in pivot.columns],
            y=pivot.index,
            colorscale="YlOrRd",
            hovertemplate="<b>%{y}</b><br>Heure: %{x}<br>Occurrences: %{z}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"Répartition des {top_n} sons principaux sur 24h",
        xaxis_title="Heure",
        yaxis_title="Type de son",
        height=500,
        margin=dict(l=150, r=20, t=50, b=40),
    )

    return fig


def create_top_sounds_bar(top_sounds: List[Dict], top_n: int = 10) -> go.Figure:
    """
    Crée le graphique en barres des sons les plus fréquents.

    Args:
        top_sounds: Liste de dicts avec label, percentage, family, is_problematic
        top_n: Nombre de sons à afficher

    Returns:
        Figure Plotly
    """
    sounds = top_sounds[:top_n]

    labels = [s["label"] for s in sounds]
    values = [s["percentage"] for s in sounds]
    colors = ["#FF6B6B" if s["is_problematic"] else "#4ECDC4" for s in sounds]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v}%" for v in values],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>%{x}% du temps<extra></extra>",
        )
    )

    fig.update_layout(
        title="Top 10 des sons détectés",
        xaxis_title="Pourcentage du temps",
        yaxis_title="",
        height=400,
        margin=dict(l=150, r=20, t=50, b=40),
        yaxis=dict(categoryorder="total ascending"),
    )

    # Ajoute une légende pour les couleurs
    fig.add_annotation(
        x=0.95,
        y=0.05,
        xref="paper",
        yref="paper",
        text="🔴 Problématique | 🟢 Normal",
        showarrow=False,
        font=dict(size=10),
    )

    return fig


def generate_all_charts(analysis: Dict, df: pd.DataFrame) -> Dict[str, go.Figure]:
    """
    Génère tous les graphiques en un seul appel.

    Args:
        analysis: Résultat de generate_full_analysis()
        df: DataFrame original (pour la heatmap)

    Returns:
        Dictionnaire avec tous les graphiques Plotly
    """
    return {
        "gauge": create_dps_gauge(
            analysis["global"]["db_mean"], analysis["global"]["note_globale"]
        ),
        "rating_bars": create_rating_bars(analysis["ratings"]["distribution"]),
        "family_pie": create_family_pie(analysis["sounds"]["families"]),
        "day_night": create_day_night_comparison(analysis["day_night"]),
        "hourly_heatmap": create_hourly_heatmap(analysis["hourly"]),
        "sounds_heatmap": create_sounds_heatmap(df),
        "top_sounds": create_top_sounds_bar(analysis["sounds"]["top_20"]),
    }


# =============================================================================
# TEST DU MODULE
# =============================================================================

if __name__ == "__main__":
    from src.data_loader import DataLoader
    from src.aggregator import generate_full_analysis

    print("\n" + "=" * 60)
    print("TEST CHARTS")
    print("=" * 60 + "\n")

    # Charge les données
    loader = DataLoader("data/dps_analysis_pi3_exemple.json")
    df = loader.load()

    # Génère l'analyse
    analysis = generate_full_analysis(df)

    # Génère tous les graphiques
    charts = generate_all_charts(analysis, df)

    print(f"✅ {len(charts)} graphiques générés :")
    for name in charts.keys():
        print(f"   - {name}")

    # Sauvegarde un exemple en HTML pour vérifier
    print("\n📊 Sauvegarde des graphiques en HTML...")

    for name, fig in charts.items():
        filepath = f"output/chart_{name}.html"
        fig.write_html(filepath)
        print(f"   ✅ {filepath}")

    print("\n🎉 Ouvre les fichiers HTML dans ton navigateur pour voir les graphiques !")
