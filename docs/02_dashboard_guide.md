# 02. 대시보드 사용 가이드

팀의 정적 시각화를 인터랙티브하게 재구성한 Streamlit 앱.

## 실행

```bash
pip install -r requirements.txt
python src/preprocess.py          # data/processed/caers_clean.csv 생성
python src/signal_detection.py    # data/processed/brand_signals.csv 생성
streamlit run app/dashboard.py
```

브라우저에서 `http://localhost:8501` 자동 열림.

## 화면 구성

| 영역 | 내용 |
| --- | --- |
| 사이드바 | 심각도 티어(severe/serious) 토글, 식품군·연령대·연도 필터 |
| KPI | 신고 수, 심각율, 분석 브랜드 수, 급증 탐지 브랜드 수 |
| 식품군 심각율 | 필터 반영 막대 (Dietary Conv 분리 효과 확인 가능) |
| 연령대×식품군 히트맵 | 취약 계층 교차 (영유아→유아식 등) |
| 연도별 추이 | 전체 vs 심각 신고 라인 |
| 브랜드 신호맵 | 신고량 vs 고위험율 산점도, 점 크기=watch_score |
| watch_score 랭킹 | 자동 탐지 상위 브랜드 표 |
| 브랜드 드릴다운 | 선택 브랜드 연도별 추이 + 실제 리콜 연도 표시 |

## 팁

- 심각도 티어를 **severe**로 두면 실제 고위험(사망/입원 등) 중심, **serious**로 두면
  FDA 광의 기준. 두 값 차이 자체가 인사이트(docs/00 참고).
- 드릴다운에서 `OXYELITE PRO`, `HYDROXYCUT`, `CHOBANI YOGURT`를 선택하면
  급증과 실제 리콜 연도(빨간 점선)가 정렬되는 검증 사례를 볼 수 있다.
