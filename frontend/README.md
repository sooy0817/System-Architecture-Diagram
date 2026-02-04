# 구성도 생성 도구 - 프론트엔드

React 기반의 구성도 생성 도구 프론트엔드입니다.

## 설치 및 실행

### 1. 의존성 설치
```bash
cd frontend
npm install
```

### 2. 개발 서버 실행
```bash
npm start
```

브라우저에서 `http://localhost:3000`으로 접속합니다.

### 3. 백엔드 서버 실행 (별도 터미널)
```bash
# 프로젝트 루트에서
cd ..
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 사용 방법

### 1단계: 법인/센터 입력
- 법인명 입력 (예: "은행")
- 센터 목록 입력 (예: "의왕", "안성")

### 2단계: 네트워크 정보 입력
- 각 센터별 네트워크 영역 입력 (예: "내부망, DMZ망")
- 장비 정보 입력 (선택사항)
- 외부 네트워크 추가 (선택사항)

### 3단계: 스코프 상세 정보 입력
- 생성된 각 스코프에 대해 순차적으로 상세 정보 입력
- 서버, 장비, 연결 정보 등을 자유 텍스트로 입력

### 4단계: 연결 관계 정의
- 스코프 간 연결 관계를 헤더 형식으로 구분하여 입력
- 통신 흐름과 보안 정책 등을 상세히 기술

### 5단계: 완료
- 모든 정보가 처리되어 구성도 생성 완료

## 기술 스택

- **React 18** - UI 프레임워크
- **TypeScript** - 타입 안전성
- **Tailwind CSS** - 스타일링
- **Heroicons** - 아이콘
- **Axios** - HTTP 클라이언트

## API 연동

백엔드 API와 연동하여 다음 엔드포인트를 사용합니다:

- `POST /sessions/` - 세션 생성
- `POST /steps/{run_id}/corp-center` - 법인/센터 정보
- `POST /steps/{run_id}/networks` - 네트워크 정보
- `POST /steps/{run_id}/next-scope` - 다음 스코프 가져오기
- `POST /steps/{run_id}/scope-detail` - 스코프 상세 정보
- `POST /steps/{run_id}/edges` - 연결 관계 정보

## 개발 참고사항

- 백엔드 서버가 `http://localhost:8000`에서 실행되어야 합니다
- CORS가 설정되어 있어 개발 환경에서 바로 연동 가능합니다
- 모든 API 호출은 `src/api/client.ts`에서 관리됩니다