from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA = Path("data")
BASE_DIR = DATA / "resultados\snapshot=20260630_142121"
OUTPUT_DIR = DATA / "last_review" / "geometry" / "dist"
CACHE_DIR = DATA / "last_review" / "geometry" / "prov"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(OUTPUT_DIR.parent.parent / "last_results.csv")
# ganador (no puede )
df2 = df[df["porcentaje_votos_validos"] > 50].copy()
df2["diff_p50"] = df2["porcentaje_votos_validos"] - 50
print(df2)


ambito_labels = {
    1: "Perú",
    2: "Exterior",
}

for ambito_val, df_ambito in df2.groupby("ambito"):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Un histograma por partido
    for partido, df_partido in df_ambito.groupby("partido"):
        color = df_partido["color_partido"].iloc[0]

        ax.hist(
            df_partido["diff_p50"],
            bins=30,
            alpha=0.7,
            color=color,
            edgecolor="black",
            label=partido,
        )

    ax.set_title(
        f"Distribución de la diferencia sobre el 50% - {ambito_labels[ambito_val]}"
    )
    ax.set_xlabel("Puntos porcentuales sobre el 50%")
    ax.set_ylabel("Número de distritos")
    ax.legend(title="Partido")

    fig.tight_layout()

    out_path = (
        OUTPUT_DIR / f"histograma_diff_p50_{ambito_labels[ambito_val].lower()}.png"
    )
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    print(f"Guardado: {out_path}")
