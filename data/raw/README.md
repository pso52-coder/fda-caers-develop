# data/raw

원본 FDA CAERS CSV는 저장소에 포함하지 않았습니다.

## 필요한 파일명

```text
CAERS_ASCII_2004_2017Q2.csv
```

이 파일을 `data/raw/` 폴더에 넣으면 전체 파이프라인을 다시 실행할 수 있습니다.

```bash
python src/preprocess.py
python src/signal_detection.py
python src/build_figures.py
python src/build_dashboard_data.py
```

참고: 저장소에는 대시보드 확인용 파생 데이터(`data/processed/`)가 포함되어 있습니다.
