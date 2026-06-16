"""labels.py — 대시보드·차트 공용 한글 라벨 매핑 (피처명 가독성 개선)."""

FOOD_GROUP_KR = {
    "Supplement (Vit/Min/Prot)": "건강기능식품",
    "Dietary Conv/Meal Replace": "식사대용식",
    "Cosmetics": "화장품",
    "Bakery": "베이커리",
    "Snack": "스낵",
    "Baby Food": "유아식",
    "Dairy": "유제품",
    "Beverage": "음료",
    "Nuts/Seed": "견과/씨앗",
    "Fruit/Vegetable": "과일/채소",
    "Seafood": "수산물",
    "Cereal": "시리얼",
    "Other/Non-Food": "기타/비식품",
}

AGE_GROUP_KR = {
    "Infant (0-5)": "영유아(0-5)",
    "Youth (6-19)": "청소년(6-19)",
    "Adult (20-59)": "성인(20-59)",
    "Senior (60+)": "노인(60+)",
    "Unknown": "미상",
}
AGE_ORDER = ["Infant (0-5)", "Youth (6-19)", "Adult (20-59)", "Senior (60+)"]

# 지표(컬럼) → 화면 표기 + 한 줄 설명
METRIC_KR = {
    "total": "총 신고",
    "serious": "FDA serious",
    "severe": "고위험(severe)",
    "severe_rate": "고위험율(%)",
    "peak_year": "피크 연도",
    "peak_ratio": "급증 배수",
    "onset_year": "급증 시작연도",
    "watch_score": "위험 점수",
    "industry": "산업군",
}
METRIC_HELP = {
    "severe_rate": "전체 신고 중 사망·생명위협·입원·장애·선천이상으로 이어진 비율",
    "peak_ratio": "피크 연도 신고가 평소(중앙값) 대비 몇 배인지",
    "onset_year": "전년 대비 4배 이상 급증한 첫 연도 (리콜 발생 시점에 해당)",
    "watch_score": "고위험율 백분위×0.5 + 급증강도 백분위×0.5 (0~100)",
}

# 산업군 원문 → 짧은 한글 (대시보드 표/범례용)
INDUSTRY_KR = {
    "Vit/Min/Prot/Unconv Diet(Human/Animal)": "건강기능식품",
    "Cosmetics": "화장품",
    "Milk/Butter/Dried Milk Prod": "유제품",
    "Fishery/Seafood Prod": "수산물",
    "Nuts/Edible Seed": "견과/씨앗",
    "Dietary Conv Food/Meal Replacements": "식사대용식",
    "Baby Food Prod": "유아식",
    "Bakery Prod/Dough/Mix/Icing": "베이커리",
    "Snack Food Item": "스낵",
}

# 증상 코드(영문) → 한글 (팀 노트북 매핑 계승)
SYMPTOM_KR = {
    "ALOPECIA": "탈모", "RASH": "발진", "PRURITUS": "가려움증", "DIZZINESS": "어지러움",
    "VOMITING": "구토", "PALPITATIONS": "심장 두근거림", "DIARRHOEA": "설사",
    "NAUSEA": "메스꺼움", "DYSPNOEA": "호흡곤란", "HEADACHE": "두통",
    "ABDOMINAL PAIN": "복통", "FATIGUE": "피로", "URTICARIA": "두드러기",
    "HYPERSENSITIVITY": "과민반응",
}


def industry_short(name: str) -> str:
    return INDUSTRY_KR.get(name, str(name)[:14])
