"""
dashboard.py — FDA CAERS 식품 안전 신호 대시보드 (Streamlit)
=============================================================
팀의 정적 시각화를 인터랙티브하게 재구성 + 갈래 B 신호탐지 결과 탐색.
피처명은 한글 라벨로 노출(가독성). 설치 없이 보려면 app/dashboard.html 사용.

실행:
    pip install -r requirements.txt
    streamlit run app/dashboard.py
"""
from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE / "src"))
from labels import (FOOD_GROUP_KR, AGE_GROUP_KR, AGE_ORDER, METRIC_HELP,
                    SYMPTOM_KR, industry_short)

RECALLS = {"OXYELITE": ("OxyElite Pro", 2013), "HYDROXYCUT": ("Hydroxycut", 2009),
           "CHOBANI YOGURT": ("Chobani Yogurt", 2013)}
st.set_page_config(page_title="FDA CAERS 식품 안전 신호", layout="wide")


@st.cache_data
def load():
    df = pd.read_csv(BASE / "data" / "processed" / "caers_clean.csv")
    sig = pd.read_csv(BASE / "data" / "processed" / "brand_signals.csv", index_col=0)
    df["식품군"] = df["food_group"].map(FOOD_GROUP_KR).fillna(df["food_group"])
    df["연령대"] = df["age_group"].map(AGE_GROUP_KR).fillna(df["age_group"])
    return df, sig


df, sig = load()
st.title("🍎 FDA CAERS 식품 안전 신호 대시보드")
st.caption("4팀 「식품 부작용의 흔적을 쫓다」 프로젝트 확장 — 브랜드 단위 자동 신호탐지 레이어")

# 사이드바
st.sidebar.header("필터")
tier_label = st.sidebar.radio("심각도 기준", ["고위험(severe)", "FDA serious(광의)"])
sev = "severe" if tier_label.startswith("고위험") else "serious"
groups = ["(전체)"] + [FOOD_GROUP_KR.get(g, g) for g in sorted(df["food_group"].unique())]
g = st.sidebar.selectbox("식품군", groups)
ages = ["(전체)"] + [AGE_GROUP_KR[a] for a in AGE_ORDER]
a = st.sidebar.selectbox("연령대", ages)
yr = st.sidebar.slider("연도", 2004, 2017, (2004, 2017))

f = df[(df["year"] >= yr[0]) & (df["year"] <= yr[1])]
if g != "(전체)":
    f = f[f["식품군"] == g]
if a != "(전체)":
    f = f[f["연령대"] == a]

# KPI
c1, c2, c3, c4 = st.columns(4)
c1.metric("신고 건수", f"{len(f):,}")
c2.metric(f"{tier_label} 비율", f"{f[sev].mean()*100:.1f}%" if len(f) else "—",
          help=METRIC_HELP["severe_rate"])
c3.metric("분석 브랜드(≥20건)", f"{len(sig):,}")
c4.metric("급증 탐지 브랜드", f"{int(sig['is_spike'].sum()):,}")
st.divider()

# 식품군 심각율 + 히트맵
left, right = st.columns(2)
with left:
    st.subheader("식품군별 심각율")
    food = f[f["식품군"] != "기타/비식품"]
    if len(food):
        rate = (food.groupby("식품군")[sev].mean()*100).sort_values()
        fig = px.bar(rate, orientation="h", labels={"value": "심각율(%)", "식품군": ""})
        fig.update_traces(marker_color="#E24B4A"); fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("연령대 × 식품군 (신고 수)")
    food2 = f[(f["식품군"] != "기타/비식품") & (f["연령대"] != "미상")]
    if len(food2):
        order = [AGE_GROUP_KR[x] for x in AGE_ORDER]
        piv = pd.pivot_table(food2, index="식품군", columns="연령대",
                             values="ra_report", aggfunc="count", fill_value=0)
        piv = piv.reindex(columns=[c for c in order if c in piv.columns])
        fig = px.imshow(piv, text_auto=True, color_continuous_scale="YlOrRd", aspect="auto")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)
st.divider()

# 연도별 추이
st.subheader("연도별 신고 추이 (전체 vs 심각)")
yt = f.groupby("year").size()
ys = f[f[sev]].groupby("year").size().reindex(yt.index, fill_value=0)
fig = go.Figure()
fig.add_scatter(x=yt.index, y=yt.values, name="전체", line=dict(color="#185FA5", width=2))
fig.add_scatter(x=ys.index, y=ys.values, name=tier_label, line=dict(color="#E24B4A", width=2))
fig.update_layout(height=340, xaxis_title="연도", yaxis_title="신고 건수")
st.plotly_chart(fig, use_container_width=True)
st.caption("2017년이 낮은 것은 데이터가 2017 Q2까지만 수집됐기 때문(감소 아님).")
st.divider()

# 산업군 × 증상 (팀 분석 축 복원)
st.subheader("식품군 × 증상 (%) — 부작용 양상 차이")
sym_groups = ["화장품", "건강기능식품", "유아식", "수산물", "식사대용식", "견과/씨앗"]
food_s = f[f["식품군"].isin(sym_groups)]
if len(food_s):
    rows = []
    for grp in sym_groups:
        sub = food_s[food_s["식품군"] == grp]["symptoms"].dropna()
        tot = max(len(sub), 1)
        cnt = {s: 0 for s in SYMPTOM_KR.values()}
        for v in sub:
            for w in str(v).split(","):
                w = w.strip().upper()
                if w in SYMPTOM_KR:
                    cnt[SYMPTOM_KR[w]] += 1
        rows.append([round(cnt[s]/tot*100, 1) for s in SYMPTOM_KR.values()])
    sym_df = pd.DataFrame(rows, index=sym_groups, columns=list(SYMPTOM_KR.values()))
    fig = px.imshow(sym_df, text_auto=True, color_continuous_scale="Reds", aspect="auto")
    fig.update_layout(height=340)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("수산물·견과→급성 위장계 / 화장품→피부. 산업군마다 부작용 형태가 다름.")
st.divider()

# 브랜드 신호맵 + 랭킹
st.subheader("브랜드 신호맵 — 신고량 vs 고위험율 (점 크기=위험점수)")
plot = sig.reset_index()
plot["앵커"] = plot["brand"].apply(lambda b: next((v[0] for k, v in RECALLS.items() if k in b), ""))
plot["산업군"] = plot["industry"].apply(industry_short)
fig = px.scatter(plot, x="total", y="severe_rate", size="watch_score", color="watch_score",
                 hover_name="brand", log_x=True, color_continuous_scale="Reds", text="앵커",
                 labels={"total": "총 신고(log)", "severe_rate": "고위험율(%)", "watch_score": "위험점수"})
fig.update_traces(textposition="top center"); fig.update_layout(height=480)
st.plotly_chart(fig, use_container_width=True)
st.caption("붉은 라벨 = 실제 FDA 리콜이 확인된 검증 앵커.")

st.subheader("위험점수 상위 브랜드 (자동 탐지)")
tbl = sig.copy()
tbl["산업군"] = tbl["industry"].apply(industry_short)
tbl = tbl.rename(columns={"total": "총 신고", "severe_rate": "고위험율(%)", "peak_year": "피크연도",
                          "peak_ratio": "급증배수", "onset_year": "급증시작", "watch_score": "위험점수"})
st.dataframe(tbl[["산업군", "총 신고", "고위험율(%)", "피크연도", "급증배수", "급증시작", "위험점수"]].head(25),
             use_container_width=True)
st.caption(f"위험점수: {METRIC_HELP['watch_score']}")
st.divider()

# 브랜드 드릴다운
st.subheader("브랜드 드릴다운")
pick = st.selectbox("브랜드 선택", sig.sort_values("watch_score", ascending=False).index.tolist())
sub = df[df["brand"] == pick]
yc = sub.groupby("year").size().reindex(range(2004, 2018), fill_value=0)
d1, d2 = st.columns([2, 1])
with d1:
    fig = go.Figure()
    fig.add_bar(x=yc.index, y=yc.values, marker_color="#185FA5")
    recall = next((v[1] for k, v in RECALLS.items() if k in pick), None)
    if recall:
        fig.add_vline(x=recall, line_dash="dot", line_color="red",
                      annotation_text=f"실제 리콜 {recall}")
    fig.update_layout(height=360, xaxis_title="연도", yaxis_title="신고")
    st.plotly_chart(fig, use_container_width=True)
with d2:
    r = sig.loc[pick]
    st.metric("총 신고", f"{int(r['total']):,}")
    st.metric("고위험율(severe)", f"{r['severe_rate']:.1f}%")
    st.metric("피크 연도 / 배수", f"{int(r['peak_year'])} / {r['peak_ratio']:.0f}x")
    st.metric("위험점수", f"{r['watch_score']:.1f}")
    if r["is_spike"]:
        st.warning("⚠️ 급증 신호 탐지됨")
