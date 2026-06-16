# data/processed

GitHub에서 대시보드를 바로 실행해볼 수 있도록 파생 데이터 2개를 포함했습니다.

| 파일 | 설명 |
| --- | --- |
| `caers_clean.csv` | 전처리 기준 보정 후 생성한 분석용 데이터 |
| `brand_signals.csv` | 브랜드별 신고량, 고위험율, 급증 신호, watch_score 결과 |

원본 데이터에서 다시 생성하려면 `data/raw/README.md` 안내에 따라 원본 CSV를 배치한 뒤 실행하세요.

```bash
python src/preprocess.py
python src/signal_detection.py
```
