"""
signal_detection.py  —  갈래 B: 신규 위험 신호 탐지
=====================================================
팀이 수작업으로 찾아낸 이상치 브랜드(OxyELITE Pro, Hydroxycut)를
'알고리즘이 자동으로 잡아내는가'를 구현하고 검증한다.

왜 이게 누수(leakage)가 아닌가:
  급증 탐지는 '결과 라벨(serious)'로 'serious'를 맞히는 지도학습이 아니라,
  시간에 따른 '신고 건수'의 비정상 패턴을 잡는 비지도 탐지다.
  결과 라벨은 위험도 '설명'에만 쓰고 '예측 입력'으로 쓰지 않는다.

두 신호를 결합한다:
  (A) 정적 위험도   : 브랜드별 신고량 × 고위험(severe) 비율  → 팀의 사분면 아이디어
  (B) 시계열 급증   : 전년 대비 급증(onset)과 피크 배수      → 리콜 시점과 정렬

출력 : data/processed/brand_signals.csv  (랭킹 테이블)
검증 : OXYELITE PRO / HYDROXYCUT 이 상위에 잡히고 급증연도가 실제 리콜연도와 맞는지
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
CLEAN = BASE / "data" / "processed" / "caers_clean.csv"
OUT = BASE / "data" / "processed" / "brand_signals.csv"

MIN_REPORTS = 20      # 통계적으로 의미있는 최소 신고량 (팀 기준 계승)
YOY_JUMP = 4.0        # 전년 대비 N배 이상이면 급증(onset)으로 판정
MIN_PEAK = 10         # 피크 연도 최소 절대 건수 (노이즈 컷)
YEARS = list(range(2004, 2018))


def detect_spike(year_counts: pd.Series):
    """브랜드 1개의 연도별 건수에서 onset/peak 신호를 추출."""
    s = year_counts.reindex(YEARS, fill_value=0)
    peak_year = int(s.idxmax())
    peak = int(s.max())
    # 피크 제외 기준선(median). 0만 있으면 1로 floor.
    base = s[s.index != peak_year]
    base = base[base > 0]
    baseline = float(base.median()) if len(base) else 0.0
    peak_ratio = peak / max(baseline, 1.0)

    # onset: 전년 대비 YOY_JUMP배 이상 뛴 '첫' 연도 (리콜 시작 시점에 해당)
    onset_year, onset_ratio = None, 0.0
    prev = None
    for y in YEARS:
        c = int(s[y])
        if prev is not None and prev >= 3 and c >= MIN_PEAK:
            r = c / prev
            if r >= YOY_JUMP:
                onset_year, onset_ratio = y, r
                break
        prev = c if c > 0 else prev
    is_spike = (peak >= MIN_PEAK) and (peak_ratio >= YOY_JUMP)
    return peak_year, peak, round(peak_ratio, 1), onset_year, round(onset_ratio, 1), is_spike


def main():
    df = pd.read_csv(CLEAN)
    df = df[(df["brand"] != "") & (df["brand"] != "REDACTED")]   # 익명 노이즈 제거(팀 처리 계승)

    # (A) 브랜드 정적 집계
    agg = df.groupby("brand").agg(
        total=("serious", "size"),
        severe=("severe", "sum"),
        serious=("serious", "sum"),
        industry=("industry", lambda x: x.mode().iloc[0] if len(x.mode()) else "Unknown"),
        first_year=("year", "min"),
        last_year=("year", "max"),
    )
    agg = agg[agg["total"] >= MIN_REPORTS].copy()
    agg["severe_rate"] = (agg["severe"] / agg["total"] * 100).round(1)

    # (B) 브랜드별 시계열 급증 탐지
    rows = []
    for brand in agg.index:
        yc = df[df["brand"] == brand].groupby("year").size()
        rows.append((brand, *detect_spike(yc)))
    spike = pd.DataFrame(rows, columns=[
        "brand", "peak_year", "peak_count", "peak_ratio",
        "onset_year", "onset_ratio", "is_spike"]).set_index("brand")
    out = agg.join(spike)

    # 통합 watch_score: 고위험 비율 백분위 + 급증 강도 백분위 (0~100)
    sev_pct = out["severe_rate"].rank(pct=True)
    spk_pct = out["peak_ratio"].rank(pct=True)
    out["watch_score"] = ((sev_pct * 0.5 + spk_pct * 0.5) * 100).round(1)
    out = out.sort_values("watch_score", ascending=False)
    out.to_csv(OUT)
    print(f"[저장] {OUT}  (분석 브랜드 {len(out):,}개)")

    # ---- 검증: 실제 리콜 사건과 대조 ----
    print("\n=== 검증: 알고리즘이 팀의 수작업 발견을 재현하는가 ===")
    anchors = {
        "OXYELITE": ("OxyElite Pro", 2013, "2013-11 FDA 간손상 리콜"),
        "HYDROXYCUT": ("Hydroxycut", 2009, "2009-05 FDA 간손상 리콜"),
    }
    n = len(out)
    for kw, (label, recall_year, note) in anchors.items():
        hit = out[out.index.str.contains(kw)]
        if hit.empty:
            print(f"[{label}] 미검출"); continue
        r = hit.iloc[0]
        rank = out.index.get_loc(hit.index[0]) + 1
        onset = r["onset_year"]
        aligned = "✓" if (pd.notna(onset) and abs(int(onset) - recall_year) <= 1) or \
                          abs(int(r["peak_year"]) - recall_year) <= 1 else "✗"
        print(f"[{label}] watch_score {r['watch_score']} (상위 {rank}/{n}, {rank/n*100:.1f}%) | "
              f"onset {onset} / peak {int(r['peak_year'])} | 실제: {note} → 시점정렬 {aligned}")

    print("\n=== watch_score 상위 12개 브랜드 ===")
    show = out.head(12)[["industry", "total", "severe_rate", "peak_year", "peak_ratio", "onset_year", "watch_score"]]
    print(show.to_string())


if __name__ == "__main__":
    main()
