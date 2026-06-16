"""build_figures.py — docs/README용 핵심 차트 4종 생성."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / "data" / "processed" / "caers_clean.csv")
sig = pd.read_csv(BASE / "data" / "processed" / "brand_signals.csv", index_col=0)
FIG = BASE / "figures"
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})
BLUE, RED = "#185FA5", "#E24B4A"

# 1) 신호맵: 브랜드 신고량 vs 고위험율, 앵커 강조
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(sig["total"], sig["severe_rate"], s=np.sqrt(sig["total"])*4,
           c="#bbbbbb", alpha=0.5, edgecolor="white", linewidth=0.5)
ax.axvline(sig["total"].median(), color="gray", ls="--", alpha=0.4)
ax.axhline(sig["severe_rate"].median(), color="gray", ls="--", alpha=0.4)
for kw, color in [("OXYELITE", RED), ("HYDROXYCUT", "#7F3FBF"), ("CHOBANI YOGURT", "#1D9E75")]:
    h = sig[sig.index.str.contains(kw)].iloc[0]
    ax.scatter(h["total"], h["severe_rate"], s=180, c=color, edgecolor="black", zorder=5)
    ax.annotate(h.name.title()[:18], (h["total"], h["severe_rate"]),
                xytext=(8, 6), textcoords="offset points", fontsize=9, fontweight="bold", color=color)
ax.set_xscale("log")
ax.set_xlabel("Total Reports (log)"); ax.set_ylabel("Severe Outcome Rate (%)")
ax.set_title("Brand Signal Map — Volume vs Severity (anchors highlighted)", fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "fig1_brand_signal_map.png"); plt.close(fig)

# 2) 앵커 시계열 — 급증=리콜 시점
fig, ax = plt.subplots(figsize=(10, 5))
for kw, color, lbl, recall in [("OXYELITE", RED, "OxyElite Pro", 2013),
                               ("HYDROXYCUT", "#7F3FBF", "Hydroxycut", 2009),
                               ("CHOBANI YOGURT", "#1D9E75", "Chobani Yogurt", 2013)]:
    sub = df[df["brand"].str.contains(kw, na=False)]
    yc = sub.groupby("year").size().reindex(range(2004, 2018), fill_value=0)
    ax.plot(yc.index, yc.values, marker="o", color=color, label=lbl, linewidth=2)
    ax.axvline(recall, color=color, ls=":", alpha=0.5)
ax.set_xlabel("Year"); ax.set_ylabel("Reports")
ax.set_title("Anchor Brands: Report Spikes Align with Actual Recalls (dotted = recall year)",
             fontweight="bold")
ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(FIG / "fig2_anchor_timeseries.png"); plt.close(fig)

# 3) 식품군 심각율 — Dietary Conv 분리 효과
food = df[df["food_group"] != "Other/Non-Food"]
rate = (food.groupby("food_group")["severe"].mean()*100).sort_values()
fig, ax = plt.subplots(figsize=(9, 5))
colors = [RED if "Dietary" in g else BLUE for g in rate.index]
rate.plot.barh(ax=ax, color=colors)
for i, v in enumerate(rate): ax.text(v, i, f" {v:.1f}%", va="center", fontsize=8)
ax.set_title("Severe-Outcome Rate by Food Group\n(Dietary Conv kept SEPARATE — red)", fontweight="bold")
ax.set_xlabel("Severe rate (%)")
fig.tight_layout(); fig.savefig(FIG / "fig3_foodgroup_severe.png"); plt.close(fig)

# 4) serious 정의 비교 (팀 vs FDA표준 vs severe)
defs = {"Team flag\n(death/hosp/life)": None, "Team donut\n(+ doctor visit) 43.9%": 43.9,
        "FDA serious\n(this work)": df["serious"].mean()*100,
        "Severe tier\n(this work)": df["severe"].mean()*100}
# 팀 플래그 재현: death/hosp/life만
team = df["outcomes"].fillna("").str.upper().apply(
    lambda x: any(k in x for k in ["DEATH", "HOSPITALIZATION", "LIFE THREATENING"]))
defs["Team flag\n(death/hosp/life)"] = team.mean()*100
fig, ax = plt.subplots(figsize=(9, 5))
keys = list(defs.keys()); vals = [defs[k] for k in keys]
bars = ax.bar(keys, vals, color=["#cccccc", "#cccccc", BLUE, RED])
for b, v in zip(bars, vals): ax.text(b.get_x()+b.get_width()/2, v+0.5, f"{v:.1f}%", ha="center", fontweight="bold")
ax.set_ylabel("Serious rate (%)")
ax.set_title("Why Serious Definition Matters (same data, 4 definitions)", fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "fig4_serious_definition.png"); plt.close(fig)

print("figures 4종 생성 완료:", [p.name for p in sorted(FIG.glob('*.png'))])

# 5) 산업군(식품군) × 증상 히트맵 — 팀 분석 축 복원
import sys
sys.path.append(str(Path(__file__).resolve().parent))
from labels import FOOD_GROUP_KR, SYMPTOM_KR
sym_groups = ["Cosmetics", "Supplement (Vit/Min/Prot)", "Baby Food", "Seafood",
              "Dietary Conv/Meal Replace", "Nuts/Seed"]
food_s = df[df["food_group"].isin(sym_groups)]
rows = []
for g in sym_groups:
    sub = food_s[food_s["food_group"] == g]["symptoms"].dropna()
    tot = max(len(sub), 1)
    cnt = {s: 0 for s in SYMPTOM_KR.values()}
    for v in sub:
        for w in str(v).split(","):
            w = w.strip().upper()
            if w in SYMPTOM_KR:
                cnt[SYMPTOM_KR[w]] += 1
    rows.append([cnt[s] / tot * 100 for s in SYMPTOM_KR.values()])
import numpy as _np
fig, ax = plt.subplots(figsize=(12, 5))
arr = _np.array(rows)
im = ax.imshow(arr, cmap="Reds", aspect="auto")
ax.set_xticks(range(len(SYMPTOM_KR))); ax.set_xticklabels(list(SYMPTOM_KR.keys()), rotation=40, ha="right", fontsize=8)
ax.set_yticks(range(len(sym_groups))); ax.set_yticklabels(sym_groups, fontsize=8)
for i in range(arr.shape[0]):
    for j in range(arr.shape[1]):
        ax.text(j, i, f"{arr[i,j]:.0f}", ha="center", va="center", fontsize=7,
                color="black" if arr[i,j] < arr.max()*0.5 else "white")
ax.set_title("Food Group x Symptom (%) — distinct adverse-event profiles", fontweight="bold")
fig.colorbar(im, ax=ax, label="% of reports")
fig.tight_layout(); fig.savefig(FIG / "fig5_symptom_heatmap.png"); plt.close(fig)
print("fig5 (증상 히트맵) 추가 생성")
