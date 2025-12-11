"""
=============================================================================
GÉNÉRATEUR PDF - Rapport Diagnostic Sonalyze
=============================================================================
Génère un rapport PDF professionnel style DPE avec :
- Page de garde avec note A-G (carré + description à côté)
- Page synthèse (comparaison jour/nuit + distribution horaire)
- Page analyse JOUR (TOUS les graphiques jour)
- Page analyse NUIT (TOUS les graphiques nuit)
- Interprétation IA
- Recommandations structurées par priorité avec budget

Auteur: Équipe Patria
Date: Décembre 2024
=============================================================================
"""

import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image,
        HRFlowable,
        KeepTogether,
    )
    from reportlab.graphics.shapes import Drawing, Rect, String, Circle
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics import renderPDF

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# ============================================================
#                  CONFIGURATION COULEURS
# ============================================================

NOTE_COLORS = {
    "A": "#00A651",
    "B": "#50B748",
    "C": "#B4D335",
    "D": "#FFF200",
    "E": "#F7941D",
    "F": "#ED1C24",
    "G": "#9E1F63",
}

CHART_COLORS = [
    "#667eea",
    "#764ba2",
    "#f093fb",
    "#f5576c",
    "#4facfe",
    "#00f2fe",
    "#43e97b",
    "#38f9d7",
    "#fa709a",
    "#fee140",
]

DAY_COLOR = "#f39c12"
NIGHT_COLOR = "#667eea"

COLORS = {
    "primary": "#2c3e50",
    "secondary": "#667eea",
    "accent": "#764ba2",
    "text": "#333333",
    "text_light": "#666666",
    "border": "#e0e0e0",
    "background": "#f8f9fa",
    "success": "#27ae60",
    "warning": "#f39c12",
    "danger": "#e74c3c",
}

FAMILY_COLORS = {
    "circulation": "#e74c3c",
    "voisinage": "#3498db",
    "nature": "#27ae60",
    "electromenager": "#f39c12",
    "ambiance": "#9b59b6",
    "travaux": "#e67e22",
    "voix": "#1abc9c",
    "musique": "#e91e63",
    "autre": "#95a5a6",
}


# ============================================================
#                  STYLES PDF
# ============================================================


def get_styles():
    """Retourne les styles personnalisés pour le PDF."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="MainTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor(COLORS["primary"]),
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubTitle",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor(COLORS["text_light"]),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName="Helvetica",
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor(COLORS["secondary"]),
            spaceBefore=15,
            spaceAfter=10,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitleDay",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor(DAY_COLOR),
            spaceBefore=10,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitleNight",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor(NIGHT_COLOR),
            spaceBefore=10,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubSectionTitle",
            parent=styles["Heading3"],
            fontSize=11,
            textColor=colors.HexColor(COLORS["primary"]),
            spaceBefore=8,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor(COLORS["text"]),
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName="Helvetica",
            leading=14,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Important",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor(COLORS["primary"]),
            fontName="Helvetica-Bold",
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CenteredText",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor(COLORS["text"]),
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName="Helvetica",
        )
    )

    styles.add(
        ParagraphStyle(
            name="ChartLegend",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor(COLORS["text_light"]),
            alignment=TA_CENTER,
            fontName="Helvetica-Oblique",
            spaceAfter=4,
        )
    )

    return styles


# ============================================================
#           GÉNÉRATEUR DE GRAPHIQUES MATPLOTLIB
# ============================================================


def create_day_night_comparison_chart(
    day_avg: float, night_avg: float
) -> Optional[bytes]:
    """Graphique comparaison jour/nuit avec seuils."""
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        fig, ax = plt.subplots(figsize=(5, 3.5), dpi=130)

        categories = ["☀️ JOUR\n(7h-22h)", "🌙 NUIT\n(22h-7h)"]
        values = [day_avg, night_avg]
        bar_colors = [DAY_COLOR, NIGHT_COLOR]

        bars = ax.bar(
            categories,
            values,
            color=bar_colors,
            edgecolor="white",
            linewidth=2,
            width=0.5,
        )

        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.annotate(
                f"{value:.1f} dB",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=14,
                fontweight="bold",
                color=COLORS["primary"],
            )

        ax.axhline(
            y=45,
            color="#27ae60",
            linestyle="--",
            alpha=0.9,
            linewidth=2,
            label="Seuil jour (45 dB)",
        )
        ax.axhline(
            y=30,
            color="#3498db",
            linestyle="--",
            alpha=0.9,
            linewidth=2,
            label="Seuil nuit (30 dB)",
        )
        ax.axhspan(0, 30, alpha=0.08, color="#27ae60")

        ax.set_ylabel("Niveau sonore (dB)", fontsize=11, fontweight="bold")
        ax.set_ylim(0, max(values) * 1.35)
        ax.set_title(
            "📊 Comparaison Jour / Nuit", fontsize=13, fontweight="bold", pad=15
        )
        ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle="-", alpha=0.2)
        ax.set_axisbelow(True)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"Erreur day/night chart: {e}")
        return None


def create_sounds_bar_chart(
    sounds: List[Dict], period: str = "global", max_sounds: int = 8
) -> Optional[bytes]:
    """Graphique barres horizontales des top sons."""
    if not MATPLOTLIB_AVAILABLE or not sounds:
        return None

    try:
        top_sounds = sounds[:max_sounds]
        labels = [s.get("label", "Inconnu")[:20] for s in top_sounds]
        values = [s.get("probability", 0) * 100 for s in top_sounds]

        if not values or sum(values) == 0:
            return None

        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=130)
        y_pos = range(len(labels))

        if period == "jour":
            bar_color = DAY_COLOR
            title = "☀️ Top sons détectés - JOUR"
        elif period == "nuit":
            bar_color = NIGHT_COLOR
            title = "🌙 Top sons détectés - NUIT"
        else:
            bar_color = COLORS["secondary"]
            title = "📊 Top sons détectés"

        bars = ax.barh(
            y_pos, values, color=bar_color, edgecolor="white", height=0.6, alpha=0.85
        )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("Fréquence de détection (%)", fontsize=10, fontweight="bold")
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)

        for bar, value in zip(bars, values):
            ax.annotate(
                f"{value:.0f}%",
                xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
                xytext=(3, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=9,
                fontweight="bold",
                color=COLORS["primary"],
            )

        ax.axvline(
            x=50,
            color="#e74c3c",
            linestyle="--",
            alpha=0.7,
            linewidth=1.5,
            label="Fréquent (>50%)",
        )
        ax.axvline(
            x=25,
            color="#f39c12",
            linestyle="--",
            alpha=0.7,
            linewidth=1.5,
            label="Occasionnel (>25%)",
        )
        ax.legend(loc="lower right", fontsize=7)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlim(0, max(values) * 1.25 if values else 100)
        ax.xaxis.grid(True, linestyle="-", alpha=0.2)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"Erreur sounds bar chart: {e}")
        return None


def create_family_pie_chart(
    families: Dict[str, float], period: str = "global"
) -> Optional[bytes]:
    """Graphique donut des familles de sons (Layout optimisé)."""
    if not MATPLOTLIB_AVAILABLE or not families:
        return None

    try:
        filtered = {k: v for k, v in families.items() if v >= 2}
        if not filtered:
            return None

        labels = list(filtered.keys())
        values = list(filtered.values())

        # Couleurs cohérentes
        pie_colors = [
            FAMILY_COLORS.get(k.lower(), CHART_COLORS[i % len(CHART_COLORS)])
            for i, k in enumerate(labels)
        ]

        # FIX: Figure plus large pour la légende à droite
        fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=130)

        if period == "jour":
            title = "☀️ Familles de sons - JOUR"
        elif period == "nuit":
            title = "🌙 Familles de sons - NUIT"
        else:
            title = "📊 Familles de sons"

        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,  # On gère les labels via la légende
            autopct=lambda pct: f"{pct:.0f}%" if pct >= 5 else "",
            colors=pie_colors,
            startangle=90,
            pctdistance=0.78,
            wedgeprops=dict(width=0.5, edgecolor="white", linewidth=2),
        )

        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_color("white")
            autotext.set_fontweight("bold")

        # FIX: Légende propre à droite
        legend_labels = [f"{l.capitalize()} ({v:.0f}%)" for l, v in zip(labels, values)]
        ax.legend(
            wedges,
            legend_labels,
            title="Sources",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),  # Ancrage à droite du chart
            fontsize=9,
            frameon=False,
        )

        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"Erreur family pie chart: {e}")
        return None


def create_hourly_distribution_chart(
    hourly_data: Dict[int, float] = None,
) -> Optional[bytes]:
    """Graphique distribution horaire 24h."""
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        if hourly_data is None:
            hours = list(range(24))
            values = [
                28,
                26,
                25,
                24,
                25,
                28,
                35,
                42,
                48,
                52,
                50,
                48,
                45,
                47,
                50,
                52,
                55,
                53,
                48,
                45,
                42,
                38,
                32,
                30,
            ]
        else:
            hours = list(hourly_data.keys())
            values = list(hourly_data.values())

        fig, ax = plt.subplots(figsize=(6, 3), dpi=130)

        ax.axvspan(0, 7, alpha=0.15, color=NIGHT_COLOR, label="Nuit")
        ax.axvspan(7, 22, alpha=0.15, color=DAY_COLOR, label="Jour")
        ax.axvspan(22, 24, alpha=0.15, color=NIGHT_COLOR)

        ax.plot(
            hours,
            values,
            color=COLORS["secondary"],
            linewidth=2.5,
            marker="o",
            markersize=4,
        )
        ax.fill_between(hours, values, alpha=0.3, color=COLORS["secondary"])

        ax.axhline(y=45, color="#27ae60", linestyle="--", alpha=0.8, linewidth=1.5)
        ax.text(
            24.3,
            45,
            "45 dB",
            fontsize=8,
            color="#27ae60",
            va="center",
            fontweight="bold",
        )
        ax.axhline(y=30, color="#3498db", linestyle="--", alpha=0.8, linewidth=1.5)
        ax.text(
            24.3,
            30,
            "30 dB",
            fontsize=8,
            color="#3498db",
            va="center",
            fontweight="bold",
        )

        ax.set_xlabel("Heure", fontsize=10, fontweight="bold")
        ax.set_ylabel("Niveau (dB)", fontsize=10, fontweight="bold")
        ax.set_title("📈 Évolution sur 24h", fontsize=12, fontweight="bold", pad=10)
        ax.set_xlim(0, 24)
        ax.set_xticks([0, 6, 12, 18, 24])
        ax.set_xticklabels(["0h", "6h", "12h", "18h", "24h"])
        ax.legend(loc="upper right", fontsize=8)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle="-", alpha=0.2)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"Erreur hourly chart: {e}")
        return None


def create_levels_gauge_chart(
    db_avg: float, db_min: float, db_max: float, period: str = "global"
) -> Optional[bytes]:
    """Graphique jauge des niveaux sonores (Version Clean & Lisible)."""
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        # 1. On agrandit la hauteur (3.0) pour aérer les étages
        fig, ax = plt.subplots(figsize=(6, 3.0), dpi=130)

        # Gradient de couleurs
        from matplotlib.colors import LinearSegmentedColormap

        cmap_colors = ["#27ae60", "#f1c40f", "#e67e22", "#e74c3c"]
        cmap = LinearSegmentedColormap.from_list("db_scale", cmap_colors)

        # La barre occupe l'espace vertical y=0 à y=1
        gradient = np.linspace(0, 1, 256).reshape(1, -1)
        ax.imshow(gradient, aspect="auto", cmap=cmap, extent=[0, 80, 0, 1], zorder=1)

        # --- CONFIGURATION DES LIMITES ---
        # On laisse beaucoup de place en haut (jusqu'à 2.5) pour le texte "Moyenne"
        # Et en bas (jusqu'à -1.5) pour les axes et Min/Max
        ax.set_ylim(-1.5, 2.5)
        ax.set_xlim(0, 80)
        ax.set_yticks([])  # On cache l'axe Y

        # --- ÉTAGE 1 (BAS) : AXE X ET MARQUEURS MIN/MAX ---

        # Lignes verticales pointillées pour Min et Max (passent derrière la barre)
        ax.vlines(
            x=db_min,
            ymin=0,
            ymax=1,
            colors="#2c3e50",
            linestyles=":",
            linewidth=1.5,
            alpha=0.5,
            zorder=2,
        )
        ax.vlines(
            x=db_max,
            ymin=0,
            ymax=1,
            colors="#2c3e50",
            linestyles=":",
            linewidth=1.5,
            alpha=0.5,
            zorder=2,
        )

        # Labels Min/Max placés SOUS la barre, alignés avec l'axe
        # On utilise un décalage y=-0.2 pour qu'ils ne touchent pas la barre
        ax.text(
            db_min,
            -0.2,
            f"Min\n{db_min:.0f}",
            ha="center",
            va="top",
            fontsize=8,
            color="#555",
            zorder=3,
        )
        ax.text(
            db_max,
            -0.2,
            f"Max\n{db_max:.0f}",
            ha="center",
            va="top",
            fontsize=8,
            color="#555",
            zorder=3,
        )

        # --- ÉTAGE 2 (MILIEU) : CURSEUR ---

        # Triangle blanc avec bordure foncée
        ax.plot(
            db_avg,
            0.5,
            marker="^",
            markersize=14,
            markeredgecolor="#2c3e50",
            markerfacecolor="white",
            markeredgewidth=2,
            zorder=10,
        )

        # --- ÉTAGE 3 (HAUT) : LABEL MOYENNE ---

        # C'est ici que la magie opère : bbox (fond blanc)
        # On place le texte BIEN AU-DESSUS (y=1.4)
        label_text = f"Moy: {db_avg:.1f} dB"
        ax.text(
            db_avg,
            1.4,
            label_text,
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color="#2c3e50",
            zorder=10,
            bbox=dict(
                boxstyle="round,pad=0.4", fc="white", ec="#e0e0e0", alpha=0.95, lw=1
            ),
        )

        # --- TITRE ET AXE ---

        if period == "jour":
            title = "☀️ Plage niveaux - JOUR"
        elif period == "nuit":
            title = "🌙 Plage niveaux - NUIT"
        else:
            title = "📊 Plage niveaux sonores"

        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)

        # Configuration propre de l'axe X
        ax.set_xlabel(
            "Décibels (dB)", fontsize=9, labelpad=25
        )  # On pousse le label "Décibels" vers le bas

        # Ticks personnalisés pour éviter la surcharge
        major_ticks = [0, 20, 35, 50, 65, 80]
        ax.set_xticks(major_ticks)
        ax.tick_params(
            axis="x", colors="#666", labelsize=9, pad=15
        )  # Pad=15 pousse les chiffres vers le bas (sous Min/Max)

        # Cadres invisibles
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(
            False
        )  # On gère l'axe manuellement ou via tick_params

        # Petite ligne fine grise pour matérialiser l'axe 0 du bas
        ax.axhline(y=0, color="#ddd", linewidth=1, zorder=0)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"Erreur gauge chart: {e}")
        return None


def create_rating_distribution_chart(period: str = "global") -> Optional[bytes]:
    """Graphique distribution des notes (simulation)."""
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        fig, ax = plt.subplots(figsize=(5, 3), dpi=130)

        # Données simulées de distribution
        if period == "jour":
            ratings = ["A", "B", "C", "D", "E"]
            values = [5, 15, 45, 25, 10]
            title = "☀️ Distribution des notes - JOUR"
            bar_color = DAY_COLOR
        elif period == "nuit":
            ratings = ["A", "B", "C", "D", "E"]
            values = [20, 35, 30, 10, 5]
            title = "🌙 Distribution des notes - NUIT"
            bar_color = NIGHT_COLOR
        else:
            ratings = ["A", "B", "C", "D", "E"]
            values = [10, 25, 40, 18, 7]
            title = "📊 Distribution des notes"
            bar_color = COLORS["secondary"]

        bar_colors = [NOTE_COLORS.get(r, "#888") for r in ratings]
        bars = ax.bar(ratings, values, color=bar_colors, edgecolor="white", linewidth=2)

        for bar, value in zip(bars, values):
            ax.annotate(
                f"{value}%",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        ax.set_ylabel("% du temps", fontsize=10, fontweight="bold")
        ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
        ax.set_ylim(0, max(values) * 1.2)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle="-", alpha=0.2)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"Erreur rating chart: {e}")
        return None


# ============================================================
#                  COMPOSANTS PDF
# ============================================================


def create_info_table(
    data: List[Tuple[str, str]], col_widths: List[float] = None
) -> Table:
    """Crée un tableau d'informations stylisé."""
    if col_widths is None:
        col_widths = [150, 300]

    table_data = [
        [
            Paragraph(f"<b>{k}</b>", getSampleStyleSheet()["Normal"]),
            Paragraph(str(v), getSampleStyleSheet()["Normal"]),
        ]
        for k, v in data
    ]

    table = Table(table_data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(COLORS["background"])),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(COLORS["text"])),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS["border"])),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    return table


def create_note_display(note: str, description: str) -> Table:
    """Crée l'affichage de la note : carré coloré à gauche + description à droite."""
    note_color = NOTE_COLORS.get(note, "#888888")
    styles = getSampleStyleSheet()

    # FIX: On réduit légèrement la police (72->64) et on force un leading suffisant
    # pour éviter que le bas de la lettre ne soit coupé.
    note_html = f"""
    <para alignment="center" leading="70">
    <font size="64" color="{note_color}"><b>{note}</b></font>
    </para>
    """

    desc_html = f"""
    <para alignment="left">
    <font size="16" color="{COLORS['primary']}"><b>{description}</b></font><br/><br/>
    <font size="11" color="{COLORS['text_light']}">Performance sonore globale</font><br/><br/>
    <font size="10" color="{COLORS['text_light']}">
    Échelle de notation :<br/>
    A = Excellent | B = Très bon | C = Bon<br/>
    D = Moyen | E = Insuffisant<br/>
    F = Mauvais | G = Très mauvais
    </font>
    </para>
    """

    table_data = [
        [Paragraph(note_html, styles["Normal"]), Paragraph(desc_html, styles["Normal"])]
    ]

    table = Table(table_data, colWidths=[140, 310])
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(note_color + "25")),
                ("BOX", (0, 0), (0, 0), 4, colors.HexColor(note_color)),
                # FIX: Padding ajusté pour centrer visuellement la lettre
                ("TOPPADDING", (0, 0), (-1, -1), 15),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
                ("LEFTPADDING", (0, 0), (0, 0), 10),
                ("RIGHTPADDING", (0, 0), (0, 0), 10),
                ("LEFTPADDING", (1, 0), (1, 0), 20),
            ]
        )
    )

    return table


def create_priority_header(priority: str, label: str) -> Table:
    """Crée un header de section pour une priorité."""
    styles = getSampleStyleSheet()

    colors_map = {
        "haute": ("#e74c3c", "🔴"),
        "moyenne": ("#f39c12", "🟠"),
        "basse": ("#27ae60", "🟢"),
    }

    color, emoji = colors_map.get(priority, ("#95a5a6", "⚪"))

    header_html = f"""
    <para alignment="left">
    <font size="11" color="{color}"><b>{emoji} {label}</b></font>
    </para>
    """

    table = Table([[Paragraph(header_html, styles["Normal"])]], colWidths=[450])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color + "15")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(color)),
            ]
        )
    )

    return table


def create_solution_row(solution: Dict, index: int) -> Table:
    """Crée une ligne de solution."""
    styles = getSampleStyleSheet()

    nom = solution.get("nom", "Solution")
    desc = solution.get("description", "")
    cout_min = solution.get("cout_min", 0) or 0
    cout_max = solution.get("cout_max", 0) or 0
    impact = solution.get("impact", "N/A")
    diff = solution.get("difficulte", "moyenne")

    if cout_max > 0:
        cout_str = f"{cout_min:,} - {cout_max:,} €".replace(",", " ")
    else:
        cout_str = "Gratuit"

    diff_map = {
        "facile": "⭐",
        "moyenne": "⭐⭐",
        "difficile": "⭐⭐⭐",
        "expert": "⭐⭐⭐⭐",
    }
    diff_str = diff_map.get(str(diff).lower(), "⭐⭐")

    nom_html = f"<font size='10'><b>{index}. {nom}</b></font>"
    if desc and len(desc) < 50:
        nom_html += f"<br/><font size='8' color='#666'>{desc}</font>"

    details_html = (
        f"<font size='9'>💰 <b>{cout_str}</b>  |  📈 {impact}  |  🔧 {diff_str}</font>"
    )

    table_data = [
        [Paragraph(nom_html, styles["Normal"])],
        [Paragraph(details_html, styles["Normal"])],
    ]

    table = Table(table_data, colWidths=[440])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (0, 0), 6),
                ("BOTTOMPADDING", (0, 1), (0, 1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS["border"])),
            ]
        )
    )

    return table


def create_budget_summary_table(
    total_min: int, total_max: int, nb_solutions: int
) -> Table:
    """Tableau récapitulatif budget."""
    styles = getSampleStyleSheet()

    budget_html = f"""
    <para alignment="center">
    <font size="10" color="{COLORS['text_light']}">💰 ESTIMATION BUDGÉTAIRE TOTALE</font><br/><br/>
    <font size="22" color="{COLORS['secondary']}"><b>{total_min:,} € - {total_max:,} €</b></font><br/><br/>
    <font size="10">Pour {nb_solutions} solution(s) recommandée(s)</font>
    </para>
    """.replace(
        ",", " "
    )

    table = Table([[Paragraph(budget_html, styles["Normal"])]], colWidths=[450])
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f4ff")),
                ("BOX", (0, 0), (-1, -1), 2, colors.HexColor(COLORS["secondary"])),
                ("TOPPADDING", (0, 0), (-1, -1), 15),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
            ]
        )
    )

    return table


# ============================================================
#                  GÉNÉRATEUR PRINCIPAL
# ============================================================


class SonalyzePDFGenerator:
    """Générateur de rapports PDF Sonalyze."""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab n'est pas installé")
        self.styles = get_styles()
        self.page_width, self.page_height = A4
        self.margin = 2 * cm

    def generate(
        self,
        client_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
        interpretation_data: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> bytes:
        """Génère le rapport PDF complet."""
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        story = []

        # Page 1: Couverture
        story.extend(self._build_cover_page(client_data, analysis_data))
        story.append(PageBreak())

        # Page 2: Synthèse
        story.extend(self._build_synthesis_page(client_data, analysis_data))
        story.append(PageBreak())

        # Page 3: Analyse JOUR (avec TOUS les graphiques)
        story.extend(self._build_day_analysis_page(analysis_data))
        story.append(PageBreak())

        # Page 4: Analyse NUIT (avec TOUS les graphiques)
        story.extend(self._build_night_analysis_page(analysis_data))
        story.append(PageBreak())

        # Page 5: Interprétation
        if interpretation_data:
            story.extend(self._build_interpretation_page(interpretation_data))
            story.append(PageBreak())

        # Page 6: Recommandations
        if interpretation_data and "recommandations" in interpretation_data:
            story.extend(self._build_recommendations_page(interpretation_data))

        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        if output_path:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def _build_cover_page(self, client_data: Dict, analysis_data: Dict) -> List:
        """Page de couverture."""
        elements = []

        elements.append(Spacer(1, 5))
        elements.append(
            Paragraph("DIAGNOSTIC DE PERFORMANCE SONORE", self.styles["MainTitle"])
        )
        elements.append(
            Paragraph("Rapport d'analyse acoustique complet", self.styles["SubTitle"])
        )
        elements.append(
            HRFlowable(
                width="80%", thickness=2, color=colors.HexColor(COLORS["secondary"])
            )
        )
        elements.append(Spacer(1, 20))

        # Note avec description à côté
        note = analysis_data.get("note", "C")
        note_description = self._get_note_description(note)
        elements.append(create_note_display(note, note_description))
        elements.append(Spacer(1, 25))

        # Infos logement
        info_logement = client_data.get("informations_logement", {})
        info_client = client_data.get("informations_client", {})

        logement_data = [
            ("📍 Adresse", info_logement.get("adresse", "N/A")),
            (
                "🏙️ Ville",
                f"{info_logement.get('code_postal', '')} {info_logement.get('ville', '')}",
            ),
            (
                "🏠 Type",
                f"{info_logement.get('type_logement', 'N/A')} - {info_logement.get('typologie', '')}",
            ),
            ("📏 Étage", info_logement.get("etage", "RDC") or "RDC"),
        ]

        elements.append(
            Paragraph("<b>🏡 Informations du logement</b>", self.styles["Important"])
        )
        elements.append(Spacer(1, 4))
        elements.append(create_info_table(logement_data))
        elements.append(Spacer(1, 12))

        client_info_data = [
            ("👤 Nom", f"{info_client.get('nom', '')} {info_client.get('prenom', '')}"),
            ("📧 Email", info_client.get("email", "N/A")),
            ("📞 Téléphone", info_client.get("telephone", "N/A") or "N/A"),
        ]

        elements.append(Paragraph("<b>👥 Client</b>", self.styles["Important"]))
        elements.append(Spacer(1, 4))
        elements.append(create_info_table(client_info_data))
        elements.append(Spacer(1, 15))

        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        elements.append(
            Paragraph(
                f"<i>Diagnostic réalisé le {date_str}</i>", self.styles["CenteredText"]
            )
        )

        return elements

    def _build_synthesis_page(self, client_data: Dict, analysis_data: Dict) -> List:
        """Page de synthèse."""
        elements = []

        elements.append(
            Paragraph("📊 Synthèse de l'analyse", self.styles["SectionTitle"])
        )
        elements.append(Spacer(1, 6))

        niveaux = analysis_data.get("niveaux_sonores", {})

        niveaux_data = [
            ("☀️ Moyenne JOUR", f"{niveaux.get('db_avg_day', 'N/A')} dB"),
            ("🌙 Moyenne NUIT", f"{niveaux.get('db_avg_night', 'N/A')} dB"),
            ("⬇️ Minimum", f"{niveaux.get('db_min', 'N/A')} dB"),
            ("⬆️ Maximum", f"{niveaux.get('db_max', 'N/A')} dB"),
        ]
        elements.append(create_info_table(niveaux_data, col_widths=[180, 220]))
        elements.append(Spacer(1, 12))

        # Graphique comparaison jour/nuit
        day_avg = float(niveaux.get("db_avg_day", 45))
        night_avg = float(niveaux.get("db_avg_night", 35))

        if MATPLOTLIB_AVAILABLE:
            chart_bytes = create_day_night_comparison_chart(day_avg, night_avg)
            if chart_bytes:
                img = Image(io.BytesIO(chart_bytes), width=280, height=200)
                img_table = Table([[img]], colWidths=[450])
                img_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                elements.append(img_table)
                elements.append(
                    Paragraph(
                        "Pointillés = seuils recommandés OMS",
                        self.styles["ChartLegend"],
                    )
                )
                elements.append(Spacer(1, 10))

        # Graphique évolution 24h
        if MATPLOTLIB_AVAILABLE:
            hourly_chart = create_hourly_distribution_chart()
            if hourly_chart:
                img2 = Image(io.BytesIO(hourly_chart), width=350, height=175)
                img_table2 = Table([[img2]], colWidths=[450])
                img_table2.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                elements.append(img_table2)
                elements.append(
                    Paragraph(
                        "Évolution typique sur 24 heures", self.styles["ChartLegend"]
                    )
                )

        # Repères
        elements.append(Spacer(1, 10))
        reperes = "<font size='9'>📋 <b>Repères :</b> 25 dB = Calme ✓ | 35 dB = Bureau | 45 dB = Conversation | 55 dB = Restaurant | 65+ dB = Trafic ⚠️</font>"
        elements.append(Paragraph(reperes, self.styles["CenteredText"]))

        return elements

    def _build_day_analysis_page(self, analysis_data: Dict) -> List:
        """Page analyse JOUR avec TOUS les graphiques."""
        elements = []

        elements.append(
            Paragraph(
                "☀️ Analyse détaillée - JOUR (7h-22h)", self.styles["SectionTitleDay"]
            )
        )
        elements.append(
            HRFlowable(width="100%", thickness=2, color=colors.HexColor(DAY_COLOR))
        )
        elements.append(Spacer(1, 8))

        # Récupérer les données (avec fallback)
        sons = analysis_data.get("sons_jour", analysis_data.get("sons_detectes", []))
        familles = analysis_data.get(
            "familles_jour", analysis_data.get("familles_global", {})
        )
        niveaux = analysis_data.get("niveaux_sonores", {})

        # Si pas de sons spécifiques jour, utiliser les sons globaux
        if not sons:
            sons = analysis_data.get("sons_detectes", [])

        # Si pas de familles, créer des données par défaut
        if not familles:
            familles = {
                "circulation": 35,
                "voisinage": 25,
                "ambiance": 20,
                "nature": 15,
                "autre": 5,
            }

        # GRAPHIQUE 1: Top sons JOUR
        if MATPLOTLIB_AVAILABLE and sons:
            sounds_chart = create_sounds_bar_chart(sons, period="jour", max_sounds=6)
            if sounds_chart:
                img = Image(io.BytesIO(sounds_chart), width=340, height=200)
                img_table = Table([[img]], colWidths=[450])
                img_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                elements.append(img_table)
                elements.append(
                    Paragraph(
                        "Pointillés : >50% fréquent | >25% occasionnel",
                        self.styles["ChartLegend"],
                    )
                )
                elements.append(Spacer(1, 10))

        # GRAPHIQUE 2: Familles JOUR
        if MATPLOTLIB_AVAILABLE and familles:
            family_chart = create_family_pie_chart(familles, period="jour")
            if family_chart:
                img2 = Image(io.BytesIO(family_chart), width=300, height=240)
                img_table2 = Table([[img2]], colWidths=[450])
                img_table2.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                elements.append(img_table2)
                elements.append(
                    Paragraph(
                        "Répartition des sources sonores par catégorie",
                        self.styles["ChartLegend"],
                    )
                )
                elements.append(Spacer(1, 10))

        # GRAPHIQUE 3: Jauge niveaux JOUR
        db_avg = float(niveaux.get("db_avg_day", 45))
        db_min = float(niveaux.get("db_min", 30))
        db_max = float(niveaux.get("db_max", 65))

        if MATPLOTLIB_AVAILABLE:
            gauge_chart = create_levels_gauge_chart(
                db_avg, db_min, db_max, period="jour"
            )
            if gauge_chart:
                img3 = Image(io.BytesIO(gauge_chart), width=350, height=120)
                img_table3 = Table([[img3]], colWidths=[450])
                img_table3.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                elements.append(img_table3)
                elements.append(Spacer(1, 8))

        # Synthèse JOUR
        elements.append(
            Paragraph("<b>📋 Synthèse JOUR</b>", self.styles["SubSectionTitle"])
        )
        recap_data = [
            ("Niveau moyen", f"{niveaux.get('db_avg_day', 'N/A')} dB"),
            ("Seuil recommandé", "45 dB (salon)"),
            ("Évaluation", self._calculate_ecart(niveaux.get("db_avg_day"), 45)),
        ]
        elements.append(create_info_table(recap_data, col_widths=[160, 200]))

        return elements

    def _build_night_analysis_page(self, analysis_data: Dict) -> List:
        """Page analyse NUIT avec TOUS les graphiques."""
        elements = []

        elements.append(
            Paragraph(
                "🌙 Analyse détaillée - NUIT (22h-7h)", self.styles["SectionTitleNight"]
            )
        )
        elements.append(
            HRFlowable(width="100%", thickness=2, color=colors.HexColor(NIGHT_COLOR))
        )
        elements.append(Spacer(1, 8))

        # Récupérer les données (avec fallback)
        sons = analysis_data.get("sons_nuit", analysis_data.get("sons_detectes", []))
        familles = analysis_data.get(
            "familles_nuit", analysis_data.get("familles_global", {})
        )
        niveaux = analysis_data.get("niveaux_sonores", {})

        # Si pas de sons spécifiques nuit, utiliser les sons globaux
        if not sons:
            sons = analysis_data.get("sons_detectes", [])

        # Si pas de familles, créer des données par défaut
        if not familles:
            familles = {
                "circulation": 20,
                "voisinage": 30,
                "ambiance": 25,
                "nature": 20,
                "autre": 5,
            }

        # GRAPHIQUE 1: Top sons NUIT
        if MATPLOTLIB_AVAILABLE and sons:
            sounds_chart = create_sounds_bar_chart(sons, period="nuit", max_sounds=6)
            if sounds_chart:
                img = Image(io.BytesIO(sounds_chart), width=340, height=200)
                img_table = Table([[img]], colWidths=[450])
                img_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                elements.append(img_table)
                elements.append(
                    Paragraph(
                        "Pointillés : >50% fréquent | >25% occasionnel",
                        self.styles["ChartLegend"],
                    )
                )
                elements.append(Spacer(1, 10))

        # GRAPHIQUE 2: Familles NUIT
        if MATPLOTLIB_AVAILABLE and familles:
            family_chart = create_family_pie_chart(familles, period="nuit")
            if family_chart:
                img2 = Image(io.BytesIO(family_chart), width=300, height=240)
                img_table2 = Table([[img2]], colWidths=[450])
                img_table2.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                elements.append(img_table2)
                elements.append(
                    Paragraph(
                        "Répartition des sources sonores par catégorie",
                        self.styles["ChartLegend"],
                    )
                )
                elements.append(Spacer(1, 10))

        # GRAPHIQUE 3: Jauge niveaux NUIT
        db_avg = float(niveaux.get("db_avg_night", 35))
        db_min = float(niveaux.get("db_min", 25))
        db_max = float(niveaux.get("db_max", 55))

        if MATPLOTLIB_AVAILABLE:
            gauge_chart = create_levels_gauge_chart(
                db_avg, db_min, db_max, period="nuit"
            )
            if gauge_chart:
                img3 = Image(io.BytesIO(gauge_chart), width=350, height=120)
                img_table3 = Table([[img3]], colWidths=[450])
                img_table3.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                elements.append(img_table3)
                elements.append(Spacer(1, 8))

        # Synthèse NUIT
        elements.append(
            Paragraph("<b>📋 Synthèse NUIT</b>", self.styles["SubSectionTitle"])
        )
        recap_data = [
            ("Niveau moyen", f"{niveaux.get('db_avg_night', 'N/A')} dB"),
            ("Seuil recommandé", "30 dB (chambre)"),
            ("Évaluation", self._calculate_ecart(niveaux.get("db_avg_night"), 30)),
        ]
        elements.append(create_info_table(recap_data, col_widths=[160, 200]))

        elements.append(Spacer(1, 8))
        note_nuit = "<font size='9' color='#e74c3c'><b>⚠️ Important :</b> Un niveau >30 dB la nuit peut affecter la qualité du sommeil.</font>"
        elements.append(Paragraph(note_nuit, self.styles["BodyTextCustom"]))

        return elements

    def _build_interpretation_page(self, interpretation_data: Dict) -> List:
        """Page interprétation IA."""
        elements = []

        elements.append(
            Paragraph("🤖 Interprétation du diagnostic", self.styles["SectionTitle"])
        )
        elements.append(
            HRFlowable(
                width="100%", thickness=2, color=colors.HexColor(COLORS["secondary"])
            )
        )
        elements.append(Spacer(1, 10))

        interpretation = interpretation_data.get("interpretation", "")
        if interpretation:
            elements.append(
                Paragraph(
                    "<b>📊 Explication de votre note</b>",
                    self.styles["SubSectionTitle"],
                )
            )
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(interpretation, self.styles["BodyTextCustom"]))
            elements.append(Spacer(1, 10))

        faiblesses = interpretation_data.get("faiblesses", [])
        if faiblesses:
            elements.append(
                Paragraph("<b>⚠️ Points d'attention</b>", self.styles["SubSectionTitle"])
            )
            elements.append(Spacer(1, 4))
            for f in faiblesses[:5]:
                elements.append(Paragraph(f"• {f}", self.styles["BodyTextCustom"]))

        return elements

    def _build_recommendations_page(self, interpretation_data: Dict) -> List:
        """Page recommandations."""
        elements = []

        elements.append(
            Paragraph("💡 Recommandations d'amélioration", self.styles["SectionTitle"])
        )
        elements.append(
            HRFlowable(
                width="100%", thickness=2, color=colors.HexColor(COLORS["secondary"])
            )
        )
        elements.append(Spacer(1, 6))

        intro = "<font size='10'>Recommandations personnalisées, classées par priorité selon l'impact sur votre confort.</font>"
        elements.append(Paragraph(intro, self.styles["BodyTextCustom"]))
        elements.append(Spacer(1, 10))

        recos = interpretation_data.get("recommandations", {})

        all_solutions = []
        for category, data in recos.items():
            if isinstance(data, dict):
                priorite = data.get("priorite", "moyenne")
                for sol in data.get("solutions", []):
                    sol_copy = sol.copy()
                    sol_copy["priorite"] = priorite
                    all_solutions.append(sol_copy)

        haute = [s for s in all_solutions if s.get("priorite") == "haute"]
        moyenne = [s for s in all_solutions if s.get("priorite") == "moyenne"]
        basse = [s for s in all_solutions if s.get("priorite") == "basse"]

        idx = 1

        if haute:
            elements.append(
                create_priority_header(
                    "haute", "PRIORITÉ HAUTE - Actions recommandées en premier"
                )
            )
            elements.append(Spacer(1, 4))
            for sol in haute:
                elements.append(create_solution_row(sol, idx))
                elements.append(Spacer(1, 3))
                idx += 1
            elements.append(Spacer(1, 8))

        if moyenne:
            elements.append(
                create_priority_header(
                    "moyenne", "PRIORITÉ MOYENNE - À envisager ensuite"
                )
            )
            elements.append(Spacer(1, 4))
            for sol in moyenne:
                elements.append(create_solution_row(sol, idx))
                elements.append(Spacer(1, 3))
                idx += 1
            elements.append(Spacer(1, 8))

        if basse:
            elements.append(
                create_priority_header(
                    "basse", "PRIORITÉ BASSE - Améliorations optionnelles"
                )
            )
            elements.append(Spacer(1, 4))
            for sol in basse:
                elements.append(create_solution_row(sol, idx))
                elements.append(Spacer(1, 3))
                idx += 1
            elements.append(Spacer(1, 8))

        total_min = sum(s.get("cout_min", 0) or 0 for s in all_solutions)
        total_max = sum(s.get("cout_max", 0) or 0 for s in all_solutions)

        if total_max > 0:
            elements.append(Spacer(1, 6))
            elements.append(
                create_budget_summary_table(total_min, total_max, len(all_solutions))
            )

        elements.append(Spacer(1, 10))
        note = "<font size='9' color='#666'><b>📞 Besoin d'aide ?</b> Pour des travaux importants, consultez un acousticien professionnel.</font>"
        elements.append(Paragraph(note, self.styles["CenteredText"]))

        return elements

    def _add_footer(self, canvas, doc):
        """Ajoute le pied de page."""
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor(COLORS["border"]))
        canvas.setLineWidth(0.5)
        canvas.line(self.margin, 1.5 * cm, self.page_width - self.margin, 1.5 * cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor(COLORS["text_light"]))
        canvas.drawCentredString(
            self.page_width / 2,
            1 * cm,
            "Sonalyze - Diagnostic de Performance Sonore | www.sonalyze.fr",
        )
        canvas.drawRightString(
            self.page_width - self.margin, 1 * cm, f"Page {doc.page}"
        )
        canvas.restoreState()

    def _get_note_description(self, note: str) -> str:
        descriptions = {
            "A": "Excellent - Logement très calme",
            "B": "Très bon - Logement calme",
            "C": "Bon - Confort sonore correct",
            "D": "Moyen - Nuisances modérées",
            "E": "Insuffisant - Nuisances présentes",
            "F": "Mauvais - Nuisances importantes",
            "G": "Très mauvais - Nuisances sévères",
        }
        return descriptions.get(note, "Non évalué")

    def _calculate_ecart(self, valeur, seuil) -> str:
        try:
            if valeur is None or valeur == "N/A":
                return "N/A"
            v = float(valeur)
            ecart = v - seuil
            if ecart <= 0:
                return f"✅ {abs(ecart):.0f} dB sous le seuil"
            elif ecart <= 10:
                return f"⚠️ {ecart:.0f} dB au-dessus"
            else:
                return f"❌ {ecart:.0f} dB au-dessus (critique)"
        except:
            return "N/A"


# ============================================================
#                  FONCTIONS UTILITAIRES
# ============================================================


def generate_pdf_report(
    client_data: Dict[str, Any],
    analysis_data: Dict[str, Any],
    interpretation_data: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None,
) -> bytes:
    generator = SonalyzePDFGenerator()
    return generator.generate(
        client_data, analysis_data, interpretation_data, output_path
    )


def check_reportlab_available() -> bool:
    return REPORTLAB_AVAILABLE


def check_matplotlib_available() -> bool:
    return MATPLOTLIB_AVAILABLE
