"""
build_dashboard_data.py
=======================
정제 데이터를 대시보드용 소형 집계로 압축하고, 데이터가 내장된
자체완결 정적 HTML 대시보드(app/dashboard.html)를 생성한다.

목적:
  - 설치(streamlit) 없이 깃헙에서/브라우저로 바로 열리는 버전 제공
  - 피처명을 한글 라벨로 노출 (가독성)
  - 팀이 했던 '산업군×증상' 분석 축 복원

출력:
  - app/dashboard_data.json   (집계 결과)
  - app/dashboard.html        (데이터 내장 정적 대시보드)
"""
import json
from pathlib import Path
import pandas as pd

import sys
sys.path.append(str(Path(__file__).resolve().parent))
from labels import (FOOD_GROUP_KR, AGE_GROUP_KR, AGE_ORDER, INDUSTRY_KR,
                    SYMPTOM_KR, industry_short)

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / "data" / "processed" / "caers_clean.csv")
sig = pd.read_csv(BASE / "data" / "processed" / "brand_signals.csv", index_col=0)

RECALLS = {"OXYELITE": ("OxyElite Pro", 2013), "HYDROXYCUT": ("Hydroxycut", 2009),
           "CHOBANI YOGURT": ("Chobani Yogurt", 2013)}
YEARS = list(range(2004, 2018))

food = df[df["food_group"] != "Other/Non-Food"]

# KPI
kpi = {
    "total": int(len(df)),
    "serious_rate": round(df["serious"].mean() * 100, 1),
    "severe_rate": round(df["severe"].mean() * 100, 1),
    "n_brands": int(len(sig)),
    "n_spike": int(sig["is_spike"].sum()),
}

# 식품군별 (양 티어)
fg = food.groupby("food_group").agg(total=("serious", "size"),
                                    serious=("serious", "mean"),
                                    severe=("severe", "mean"))
food_groups = [{
    "name": FOOD_GROUP_KR.get(g, g),
    "total": int(r.total),
    "serious_rate": round(r.serious * 100, 1),
    "severe_rate": round(r.severe * 100, 1),
} for g, r in fg.sort_values("severe", ascending=False).iterrows()]

# 연령대 × 식품군 (건수)
af = food[food["age_group"] != "Unknown"]
piv = pd.pivot_table(af, index="food_group", columns="age_group",
                     values="ra_report", aggfunc="count", fill_value=0)
piv = piv.reindex(columns=[c for c in AGE_ORDER if c in piv.columns])
age_food = {
    "ages": [AGE_GROUP_KR[c] for c in piv.columns],
    "groups": [FOOD_GROUP_KR.get(g, g) for g in piv.index],
    "z": piv.values.tolist(),
}

# 연도별 추이
yt = df.groupby("year").size().reindex(YEARS, fill_value=0)
ys = df[df["serious"]].groupby("year").size().reindex(YEARS, fill_value=0)
yv = df[df["severe"]].groupby("year").size().reindex(YEARS, fill_value=0)
yearly = {"years": YEARS, "total": yt.tolist(), "serious": ys.tolist(), "severe": yv.tolist()}

# 산업군 × 증상 (% within group) — 팀 분석 축 복원
sym_groups = ["Cosmetics", "Supplement (Vit/Min/Prot)", "Baby Food", "Seafood",
              "Dietary Conv/Meal Replace", "Nuts/Seed"]
sym_list = list(SYMPTOM_KR.values())
zmat = []
for g in sym_groups:
    sub = food[food["food_group"] == g]["symptoms"].dropna()
    tot = max(len(sub), 1)
    cnt = {s: 0 for s in SYMPTOM_KR.values()}
    for v in sub:
        for w in str(v).split(","):
            w = w.strip().upper()
            if w in SYMPTOM_KR:
                cnt[SYMPTOM_KR[w]] += 1
    zmat.append([round(cnt[s] / tot * 100, 1) for s in sym_list])
symptom = {"groups": [FOOD_GROUP_KR.get(g, g) for g in sym_groups],
           "symptoms": sym_list, "z": zmat}

# 브랜드 신호 + 연도별 추이
brands = []
for b, r in sig.iterrows():
    yc = df[df["brand"] == b].groupby("year").size().reindex(YEARS, fill_value=0)
    anchor, recall = "", None
    for kw, (lbl, ry) in RECALLS.items():
        if kw in b:
            anchor, recall = lbl, ry
    brands.append({
        "brand": b.title()[:40],
        "industry": industry_short(r["industry"]),
        "total": int(r["total"]),
        "severe_rate": float(r["severe_rate"]),
        "peak_year": int(r["peak_year"]),
        "peak_ratio": float(r["peak_ratio"]),
        "onset_year": None if pd.isna(r["onset_year"]) else int(r["onset_year"]),
        "watch_score": float(r["watch_score"]),
        "is_spike": bool(r["is_spike"]),
        "anchor": anchor, "recall": recall,
        "yearly": yc.tolist(),
    })

data = {"kpi": kpi, "food_groups": food_groups, "age_food": age_food,
        "yearly": yearly, "symptom": symptom, "years": YEARS, "brands": brands}

(BASE / "app" / "dashboard_data.json").write_text(
    json.dumps(data, ensure_ascii=False), encoding="utf-8")
print("dashboard_data.json 저장")

# ---------------- 정적 HTML 생성 ----------------
HTML = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>FDA CAERS 식품 안전 신호 대시보드</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  body{font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;margin:0;background:#f7f7f9;color:#222}
  .wrap{max-width:1180px;margin:0 auto;padding:24px}
  h1{font-size:24px;margin:0 0 4px} .sub{color:#777;margin:0 0 20px;font-size:14px}
  .kpis{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:18px}
  .kpi{background:#fff;border-radius:12px;padding:16px 20px;flex:1;min-width:150px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
  .kpi .v{font-size:26px;font-weight:700;color:#E24B4A} .kpi .l{font-size:13px;color:#666;margin-top:4px}
  .card{background:#fff;border-radius:12px;padding:18px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
  .card h2{font-size:16px;margin:0 0 10px} .row{display:flex;gap:18px;flex-wrap:wrap}
  .row>.card{flex:1;min-width:420px}
  .tier{margin-bottom:16px} .tier button{border:1px solid #ddd;background:#fff;padding:8px 14px;border-radius:8px;cursor:pointer;margin-right:6px}
  .tier button.on{background:#E24B4A;color:#fff;border-color:#E24B4A}
  select{padding:6px 10px;border-radius:8px;border:1px solid #ccc;font-size:14px}
  table{width:100%;border-collapse:collapse;font-size:13px} th,td{padding:7px 8px;border-bottom:1px solid #eee;text-align:right}
  th:first-child,td:first-child{text-align:left} thead th{color:#888;font-weight:600;border-bottom:2px solid #eee}
  .note{font-size:12px;color:#888;margin-top:6px}
  .anchor{color:#E24B4A;font-weight:700}
</style></head><body><div class="wrap">
<h1>🍎 FDA CAERS 식품 안전 신호 대시보드</h1>
<p class="sub">4팀 「식품 부작용의 흔적을 쫓다」 프로젝트 확장 — 브랜드 단위 자동 신호탐지 레이어 · 설치 불필요(정적)</p>

<div class="tier">심각도 기준:
  <button id="bt-severe" class="on" onclick="setTier('severe')">고위험(severe)</button>
  <button id="bt-serious" onclick="setTier('serious')">FDA serious(광의)</button>
</div>

<div class="kpis" id="kpis"></div>

<div class="row">
  <div class="card"><h2>식품군별 심각율</h2><div id="fg"></div></div>
  <div class="card"><h2>연령대 × 식품군 (신고 수)</h2><div id="af"></div></div>
</div>

<div class="card"><h2>연도별 신고 추이</h2><div id="yr"></div>
  <p class="note">2017년이 낮은 것은 데이터가 2017 Q2까지만 수집됐기 때문(감소 아님).</p></div>

<div class="card"><h2>식품군 × 증상 (%) — 부작용 양상 차이</h2><div id="sym"></div>
  <p class="note">수산물·견과 → 급성 위장계 / 화장품 → 피부 / 산업군마다 부작용 형태가 다름.</p></div>

<div class="card"><h2>브랜드 신호맵 — 신고량 vs 고위험율 (점 크기=위험점수)</h2><div id="sc"></div>
  <p class="note">붉은 라벨 = 실제 FDA 리콜이 확인된 검증 앵커(OxyElite Pro·Hydroxycut·Chobani).</p></div>

<div class="card"><h2>위험점수 상위 브랜드 (자동 탐지)</h2><div id="tbl"></div>
  <p class="note">위험점수 = 고위험율 백분위×0.5 + 급증강도 백분위×0.5. 급증연도가 실제 리콜연도와 정렬됨.</p></div>

<div class="card"><h2>브랜드 드릴다운</h2>
  <select id="pick" onchange="drill()"></select>
  <div id="dr" style="margin-top:10px"></div></div>

<script>
const DATA = __DATA__;
let tier = 'severe';
const C={blue:'#185FA5',red:'#E24B4A',gray:'#bbb'};
const L={severe:'고위험(severe)',serious:'FDA serious'};

function setTier(t){tier=t;
  document.getElementById('bt-severe').className=t=='severe'?'on':'';
  document.getElementById('bt-serious').className=t=='serious'?'on':'';
  render();}

function kpis(){
  const k=DATA.kpi;
  const rate = tier=='severe'?k.severe_rate:k.serious_rate;
  const cards=[['총 신고',k.total.toLocaleString()],[L[tier]+' 비율',rate+'%'],
    ['분석 브랜드(≥20건)',k.n_brands],['급증 탐지 브랜드',k.n_spike]];
  document.getElementById('kpis').innerHTML=cards.map(c=>
    `<div class="kpi"><div class="v">${c[1]}</div><div class="l">${c[0]}</div></div>`).join('');
}
function fgChart(){
  const fg=[...DATA.food_groups].sort((a,b)=>
    (tier=='severe'?a.severe_rate-b.severe_rate:a.serious_rate-b.serious_rate));
  Plotly.newPlot('fg',[{type:'bar',orientation:'h',
    y:fg.map(d=>d.name),x:fg.map(d=>tier=='severe'?d.severe_rate:d.serious_rate),
    marker:{color:C.red},text:fg.map(d=>(tier=='severe'?d.severe_rate:d.serious_rate)+'%'),
    textposition:'outside'}],
    {margin:{l:90,r:30,t:10,b:30},height:360,xaxis:{title:'심각율(%)'}},{displayModeBar:false});
}
function afChart(){
  Plotly.newPlot('af',[{type:'heatmap',z:DATA.age_food.z,x:DATA.age_food.ages,
    y:DATA.age_food.groups,colorscale:'YlOrRd',text:DATA.age_food.z,texttemplate:'%{text}',
    textfont:{size:9}}],{margin:{l:90,r:10,t:10,b:40},height:360},{displayModeBar:false});
}
function yrChart(){
  const y=DATA.yearly;
  Plotly.newPlot('yr',[
    {x:y.years,y:y.total,name:'전체',line:{color:C.blue,width:2},mode:'lines+markers'},
    {x:y.years,y:y[tier],name:L[tier],line:{color:C.red,width:2},mode:'lines+markers'}],
    {margin:{l:50,r:20,t:10,b:40},height:330,xaxis:{title:'연도'},yaxis:{title:'신고 건수'}},
    {displayModeBar:false});
}
function symChart(){
  Plotly.newPlot('sym',[{type:'heatmap',z:DATA.symptom.z,x:DATA.symptom.symptoms,
    y:DATA.symptom.groups,colorscale:'Reds',text:DATA.symptom.z,texttemplate:'%{text}',
    textfont:{size:8}}],{margin:{l:90,r:10,t:10,b:60},height:320},{displayModeBar:false});
}
function scChart(){
  const b=DATA.brands;
  Plotly.newPlot('sc',[{x:b.map(d=>d.total),y:b.map(d=>d.severe_rate),mode:'markers+text',
    marker:{size:b.map(d=>Math.max(6,d.watch_score/4)),color:b.map(d=>d.watch_score),
    colorscale:'Reds',showscale:true,line:{width:.5,color:'#999'}},
    text:b.map(d=>d.anchor),textposition:'top center',
    hovertext:b.map(d=>d.brand+'<br>위험점수 '+d.watch_score),hoverinfo:'text'}],
    {margin:{l:50,r:20,t:10,b:50},height:460,
     xaxis:{title:'총 신고(log)',type:'log'},yaxis:{title:'고위험율(%)'}},{displayModeBar:false});
}
function table(){
  const b=[...DATA.brands].sort((x,y)=>y.watch_score-x.watch_score).slice(0,20);
  let h='<table><thead><tr><th>브랜드</th><th>산업군</th><th>총 신고</th><th>고위험율</th>'+
    '<th>피크연도</th><th>급증배수</th><th>급증시작</th><th>위험점수</th></tr></thead><tbody>';
  b.forEach(d=>{h+=`<tr><td class="${d.anchor?'anchor':''}">${d.brand}</td><td>${d.industry}</td>`+
    `<td>${d.total}</td><td>${d.severe_rate}%</td><td>${d.peak_year}</td>`+
    `<td>${d.peak_ratio}x</td><td>${d.onset_year||'-'}</td><td><b>${d.watch_score}</b></td></tr>`;});
  document.getElementById('tbl').innerHTML=h+'</tbody></table>';
}
function fillPick(){
  const sel=document.getElementById('pick');
  const b=[...DATA.brands].sort((x,y)=>y.watch_score-x.watch_score);
  sel.innerHTML=b.map(d=>`<option value="${d.brand}">${d.brand}</option>`).join('');
}
function drill(){
  const name=document.getElementById('pick').value;
  const d=DATA.brands.find(x=>x.brand==name);
  const shapes=[]; let title=name;
  if(d.recall){shapes.push({type:'line',x0:d.recall,x1:d.recall,yref:'paper',y0:0,y1:1,
    line:{color:'red',dash:'dot'}});title+=` — 실제 리콜 ${d.recall} (점선)`;}
  Plotly.newPlot('dr',[{type:'bar',x:DATA.years,y:d.yearly,marker:{color:C.blue}}],
    {margin:{l:50,r:20,t:30,b:40},height:340,title:{text:title,font:{size:13}},
     shapes:shapes,xaxis:{title:'연도'},yaxis:{title:'신고'}},{displayModeBar:false});
}
function render(){kpis();fgChart();yrChart();}
afChart();symChart();scChart();table();fillPick();drill();render();
</script>
</div></body></html>"""

html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False))
(BASE / "app" / "dashboard.html").write_text(html, encoding="utf-8")
print(f"dashboard.html 저장 ({len(html)//1024} KB)")
