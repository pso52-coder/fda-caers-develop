"""
preprocess.py  —  디벨롭 레이어 전처리 (팀 베이스라인 보정판)
================================================================
팀 노트북의 전처리를 계승하되, 다음 3가지를 "더 정확한 기준"으로 통일한다.
(무엇을/왜 바꿨는지는 docs/00_changes_from_team_baseline.md에 상세 기록)

  [보정 1] serious 정의 통일 — FDA 공식 결과(Outcome) 분류를 따른다.
     팀 코드 플래그: DEATH/HOSPITALIZATION/LIFE THREATENING (3개) → 최대 카테고리
       'OTHER SERIOUS', 'SERIOUS INJURIES'를 누락(과소집계).
     팀 도넛 차트: 위에 더해 '병원방문(VISIT)'을 포함(과대집계).
     → 두 정의가 불일치. FDA 분류상 '병원방문/ER방문'은 serious가 아니므로,
       FDA serious 8개 카테고리로 단일화한다.
     추가로 'severe'(사망/생명위협/입원/장애/선천이상) 상위 티어를 분리 제공.

  [보정 2] Dietary Conv 분리 — 팀/내 1차 분석은 식사대용식을 건기식에 병합했으나,
     이 그룹의 심각 부작용 비율이 가장 높아(45%대) 병합 시 신호가 희석된다.
     별도 식품군으로 유지한다.

  [보정 3] 나이 환산 절삭 보정 — 팀 코드는 int()로 잘라 12개월 미만 영아가 0세로
     뭉개졌다. 분수(예: 3 Month → 0.25)로 보존한다.

입력 : data/raw/CAERS_ASCII_2004_2017Q2.csv
출력 : data/processed/caers_clean.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw" / "CAERS_ASCII_2004_2017Q2.csv"
OUT = BASE / "data" / "processed" / "caers_clean.csv"

# 팀 노트북과 동일한 친화적 컬럼명(연속성 유지)
RENAME = {
    "PRI_Reported Brand/Product Name": "brand",
    "SYM_One Row Coded Symptoms": "symptoms",
    "CI_Gender": "gender",
    "CI_Age at Adverse Event": "age",
    "CI_Age Unit": "age_unit",
    "RA_Report #": "ra_report",
    "RA_CAERS Created Date": "created_date",
    "AEC_Event Start Date": "start_date",
    "PRI_Product Role": "product_role",
    "PRI_FDA Industry Code": "industry_code",
    "AEC_One Row Outcomes": "outcomes",
    "PRI_FDA Industry Name": "industry",
}

# [보정 1] FDA 공식 serious 결과 카테고리 (병원/ER 방문은 제외)
SERIOUS_TOKENS = {
    "OTHER SERIOUS (IMPORTANT MEDICAL EVENTS)", "HOSPITALIZATION", "LIFE THREATENING",
    "SERIOUS INJURIES/ ILLNESS", "REQ. INTERVENTION TO PRVNT PERM. IMPRMNT.",
    "DISABILITY", "DEATH", "CONGENITAL ANOMALY",
}
# 상위 티어(생명/영구손상 직결) — 대시보드 토글용
SEVERE_TOKENS = {"DEATH", "LIFE THREATENING", "HOSPITALIZATION", "DISABILITY", "CONGENITAL ANOMALY"}

UNIT_TO_YEARS = {"Year(s)": 1.0, "Decade(s)": 10.0,
                 "Month(s)": 1/12, "Week(s)": 1/52, "Day(s)": 1/365}

# [보정 2] Dietary Conv를 별도 유지하는 식품군 매핑
FOOD_GROUP = {
    "Supplement (Vit/Min/Prot)": ["Vit/Min/Prot"],
    "Dietary Conv/Meal Replace": ["Dietary Conv", "Meal Replacement"],
    "Cosmetics": ["Cosmetics"],
    "Bakery": ["Bakery", "Dough", "Icing"],
    "Snack": ["Snack"],
    "Baby Food": ["Baby Food"],
    "Dairy": ["Milk", "Butter", "Cheese", "Ice Cream", "Yogurt"],
    "Beverage": ["Soft Drink", "Water", "Coffee", "Tea", "Juice", "Beverage"],
    "Nuts/Seed": ["Nuts", "Edible Seed"],
    "Fruit/Vegetable": ["Fruit", "Vegetable"],
    "Seafood": ["Fishery", "Seafood"],
    "Cereal": ["Cereal", "Breakfast"],
}


def to_years(age, unit):
    if pd.isna(age) or str(unit).strip() == "Not Available":
        return np.nan
    try:
        y = float(age) * UNIT_TO_YEARS.get(str(unit).strip(), np.nan)
    except (TypeError, ValueError):
        return np.nan
    if np.isnan(y) or y < 0 or y > 120:   # 이상치 제거
        return np.nan
    return round(y, 2)


def age_group(y):
    if pd.isna(y): return "Unknown"
    if y <= 5:  return "Infant (0-5)"
    if y <= 19: return "Youth (6-19)"
    if y <= 59: return "Adult (20-59)"
    return "Senior (60+)"


def food_group(industry):
    if pd.isna(industry): return "Other/Non-Food"
    name = str(industry).lower()
    for g, kws in FOOD_GROUP.items():
        if any(k.lower() in name for k in kws):
            return g
    return "Other/Non-Food"


def flag(outcomes, tokens):
    if pd.isna(outcomes): return False
    return any(t.strip() in tokens for t in str(outcomes).upper().split(","))


def main():
    df = pd.read_csv(RAW, dtype=str).rename(columns=RENAME)
    print(f"[로딩] {len(df):,}행")

    df["brand"] = df["brand"].fillna("").str.upper().str.strip()
    df["age_years"] = [to_years(a, u) for a, u in zip(df["age"], df["age_unit"])]
    df["age_group"] = df["age_years"].apply(age_group)
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["year"] = df["created_date"].dt.year
    df["food_group"] = df["industry"].apply(food_group)
    df["serious"] = df["outcomes"].apply(lambda x: flag(x, SERIOUS_TOKENS))   # 보정1
    df["severe"] = df["outcomes"].apply(lambda x: flag(x, SEVERE_TOKENS))

    df.to_csv(OUT, index=False)
    print(f"[저장] {OUT}")

    print("\n=== 검증 (팀 베이스라인 대비) ===")
    print(f"serious(FDA표준): {df['serious'].mean()*100:.1f}%  ← 팀 도넛 43.9%/팀 플래그와 상이")
    print(f"severe(상위티어): {df['severe'].mean()*100:.1f}%")
    print(f"나이 환산: 3개월→{to_years(3,'Month(s)')} (팀: int절삭으로 0)")
    print("Dietary Conv 분리 심각율: %.1f%%" %
          (df[df.food_group=='Dietary Conv/Meal Replace']['serious'].mean()*100))
    print("Supplement 심각율: %.1f%%" %
          (df[df.food_group=='Supplement (Vit/Min/Prot)']['serious'].mean()*100))


if __name__ == "__main__":
    main()
