# 04. GitHub 웹 업로드 가이드

## 1. 업로드 전 확인

이 폴더는 GitHub 저장소 루트에 바로 올릴 수 있는 형태입니다.

업로드할 때는 압축 파일 자체가 아니라, 압축을 푼 뒤 **폴더 안의 파일과 폴더 전체**를 GitHub 웹 화면에 드래그 앤 드롭하세요.

```text
README.md
requirements.txt
.gitignore
app/
data/
docs/
figures/
src/
```

## 2. GitHub 웹에서 업로드하는 방법

1. GitHub에서 새 Repository를 만듭니다.
2. `uploading an existing file` 또는 `Add file > Upload files`를 누릅니다.
3. 이 폴더 안의 전체 파일/폴더를 드래그 앤 드롭합니다.
4. 커밋 메시지를 입력합니다.

추천 커밋 메시지:

```text
Initial commit: FDA CAERS signal detection project
```

## 3. 업로드 후 확인할 것

- README 이미지가 정상 표시되는지 확인합니다.
- `app/dashboard.html`이 열리는지 확인합니다.
- `data/processed/caers_clean.csv`는 약 23MB로 GitHub 웹 업로드 제한에 가까우므로 실패하면 이 파일은 제외하고 업로드하세요.
- 제외해도 정적 대시보드(`app/dashboard.html`)와 주요 결과 문서는 확인할 수 있습니다.

## 4. GitHub Pages로 대시보드 배포하고 싶다면

1. Repository Settings로 이동합니다.
2. Pages 메뉴를 엽니다.
3. Branch를 `main`, folder를 `/root`로 설정합니다.
4. 배포 후 아래 경로로 접근합니다.

```text
https://사용자명.github.io/저장소명/app/dashboard.html
```

단, `dashboard.html`은 Plotly CDN을 사용하므로 인터넷 연결이 필요합니다.
