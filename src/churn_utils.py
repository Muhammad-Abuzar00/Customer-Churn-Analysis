"""Shared theme, palette and helpers for the Telco churn notebooks.

Keeping these in one place means every chart in the project uses the same
look, colours and export settings.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "Telco-Customer-Churn.csv"
CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "clean.csv"
IMAGES_DIR = PROJECT_ROOT / "images"

# Palette (validated categorical order: blue, orange, aqua, ...)
BLUE = "#2a78d6"      # retained / below-average risk
ORANGE = "#eb6834"    # churned / above-average risk
AQUA = "#1baf7a"
GREY = "#52514e"      # reference lines, secondary text
INK = "#0b0b0b"
GRID = "#e4e3df"

CHURN_PALETTE = {"No": BLUE, "Yes": ORANGE}

# Sequential (one hue, light -> dark) for magnitude heatmaps
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", ["#f4f8fd", "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)
# Diverging (blue <-> grey midpoint <-> red) for correlations
DIV_BLUE_RED = LinearSegmentedColormap.from_list(
    "div_blue_red", ["#184f95", "#6da7ec", "#f0efec", "#ec8a89", "#b8302f"]
)

TENURE_BANDS = ["0-12", "13-24", "25-48", "49-72"]
CONTRACT_ORDER = ["Month-to-month", "One year", "Two year"]


def set_theme():
    """Apply the project-wide seaborn/matplotlib theme."""
    sns.set_theme(
        style="whitegrid",
        context="notebook",
        rc={
            "figure.figsize": (9, 5),
            "figure.dpi": 100,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelsize": 11,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRID,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": GREY,
            "ytick.color": GREY,
            "text.color": INK,
            "font.family": "DejaVu Sans",
            "legend.frameon": False,
            "text.parse_math": False,  # show "$" literally in titles and labels
        },
    )
    sns.set_palette([BLUE, ORANGE, AQUA, "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"])


def save_fig(fig, name):
    """Save a figure to images/ as a 300 dpi PNG."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    path = IMAGES_DIR / f"{name}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    return path


def load_clean():
    """Load the processed dataset with ordered categoricals."""
    df = pd.read_csv(CLEAN_PATH)
    df["tenure_band"] = pd.Categorical(df["tenure_band"], categories=TENURE_BANDS, ordered=True)
    df["Contract"] = pd.Categorical(df["Contract"], categories=CONTRACT_ORDER, ordered=True)
    return df


def churn_table(df, col):
    """Customers, churners, churn rate and lost MRR for each level of `col`."""
    out = (
        df.groupby(col, observed=True)
        .agg(
            customers=("churn_flag", "size"),
            churned=("churn_flag", "sum"),
            churn_rate=("churn_flag", "mean"),
            mrr_lost=("MonthlyCharges", lambda s: s[df.loc[s.index, "churn_flag"] == 1].sum()),
        )
        .sort_values("churn_rate", ascending=False)
    )
    out["share_of_customers"] = out["customers"] / out["customers"].sum()
    return out


def pct_axis(ax, axis="x"):
    fmt = mtick.PercentFormatter(1.0, decimals=0)
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(fmt)


def churn_bar(df, col, title, ax=None, overall=None, xlabel="Churn rate"):
    """Sorted horizontal bar chart of churn rate by `col`.

    Bars above the overall churn rate are orange, at or below are blue, and
    a dashed line marks the overall average.
    """
    overall = df["churn_flag"].mean() if overall is None else overall
    tbl = churn_table(df, col).sort_values("churn_rate")
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 0.6 * len(tbl) + 1.6))
    colors = [ORANGE if r > overall else BLUE for r in tbl["churn_rate"]]
    ax.barh(tbl.index.astype(str), tbl["churn_rate"], color=colors, height=0.6)
    ax.axvline(overall, color=GREY, ls="--", lw=1.2)
    ax.set_ylim(-0.6, len(tbl) - 0.05)
    ax.text(overall, len(tbl) - 0.4, f" overall avg {overall:.1%}", color=GREY, fontsize=9, va="center")
    for i, (rate, n) in enumerate(zip(tbl["churn_rate"], tbl["customers"])):
        ax.text(rate + 0.006, i, f"{rate:.1%}  (n={n:,})", va="center", fontsize=9, color=INK,
                bbox=dict(facecolor="white", edgecolor="none", pad=1, alpha=0.85))
    ax.set_xlim(0, max(tbl["churn_rate"].max() * 1.3, overall * 1.3))
    pct_axis(ax, "x")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
    return ax, tbl
