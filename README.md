# Vulnerable Shopping Mall (VULN SHOP)

**"VULN SHOP"**은 교육 및 연구 목적의 취약한 웹 애플리케이션입니다.
생성형 AI를 활용한 공격 로그 분석 연구 등을 위해 의도적으로 다양한 웹 취약점을 단계별로 구현했습니다.

## 🎨 주요 특징

*   **VULN SHOP Design:** 미니멀리즘과 모노톤을 강조한 현대적인 스트릿웨어 브랜드 디자인.
*   **3단계 보안 레벨 시스템 (v1 / v2 / v3):**
    *   사용자가 UI에서 실시간으로 보안 레벨을 변경할 수 있습니다.
    *   **v1 (Low):** 보안 조치 없음. 모든 취약점에 노출됨.
    *   **v2 (Medium):** 불완전한 필터링 및 미티게이션 적용 (우회 가능).
    *   **v3 (High):** 강력한 보안 적용 (공격 방어).
*   **Admin 기능:** 관리자 계정을 통한 상품 관리, 게시글 삭제, 회원 관리 기능 제공.
*   **Docker 지원:** 컨테이너 기반으로 어디서든 쉽게 배포하고 실행할 수 있습니다.

## 🕷️ 구현된 취약점

| 취약점 (Vulnerability) | 대상 기능 | 설명 |
| :--- | :--- | :--- |
| **SQL Injection** | 로그인 | `admin' --` 등의 입력으로 인증 우회 가능. |
| **Cross-Site Scripting (XSS)** | Q&A 게시판 | 악성 스크립트(`<script>`)를 게시글에 삽입하여 실행 가능. |
| **File Upload** | 프로필 설정 | 웹쉘(.php 등) 업로드 및 원격 코드 실행(RCE) 가능성. |
| **IDOR (Insecure Direct Object References)** | 주문 내역 | URL 파라미터 변조로 타인의 주문 내역 열람 가능. |

## 🛠️ 기술 스택

*   **Frontend:** EJS, Vanilla CSS
*   **Backend:** Node.js, Express.js
*   **Database:** SQLite3
*   **Infrastructure:** Docker, Docker Compose

## ⚙️ 환경 설정 (.env)

프로젝트 루트에 `.env.example` 파일이 제공됩니다. 이 파일을 복사하여 `.env` 파일을 생성하고 설정을 변경하세요.

```bash
cp .env.example .env
```

```env
# 관리자 계정 설정
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# 보안 레벨 기본값 (v1, v2, v3)
SECURITY_LEVEL=v1

# 포트 설정 (기본값: 3000)
PORT=8765
```

## 🚀 실행 방법

### 1. Docker 사용 (권장)

가장 간편한 실행 방법입니다. Docker와 Docker Compose가 설치되어 있어야 합니다.

```bash
# 컨테이너 빌드 및 실행
docker-compose up -d --build
```

`.env` 파일에 설정된 `PORT` (기본값 3000)로 접속할 수 있습니다. 예: `http://localhost:8765`

### 2. 로컬 실행 (Node.js)

Node.js 환경이 구성되어 있어야 합니다.

```bash
# 의존성 설치
npm install

# 서버 실행
node server.js
```

## 🧪 검증 및 테스트

### 자동화된 검증
자동화된 검증 스크립트를 통해 각 보안 레벨별로 취약점이 의도대로 동작하는지 확인할 수 있습니다.

```bash
# 기본 취약점 검증
node verify_attacks_v2.js

# 관리자 기능 검증
node verify_admin.js
```

## 📡 네트워크 패킷 캡처 (NIDS 데이터)
기존 NIDS(CICIDS2018 등)와 호환되는 데이터셋을 생성하기 위해, 사이드카 컨테이너(`packet-sniffer`)가 모든 네트워크 트래픽을 `.pcap` 파일로 캡처합니다.

- **위치:** `pcap/` 디렉토리.
- **형식:** 표준 PCAP (Wireshark, tcpdump, CICFlowMeter 등에서 읽기 가능).
- **로테이션:** 파일은 매 시간마다 로테이션됩니다 (`traffic-YYYY-MM-DD-HH-MM.pcap`).

**사용 방법:**
1.  **Wireshark로 분석:** `.pcap` 파일을 열어 전체 패킷 상세 정보(Flags, Payload 등)를 확인합니다.
2.  **CSV로 변환:** **CICFlowMeter**와 같은 도구를 사용하여 AI 학습을 위한 특징(Flow Duration, Total Fwd Packets 등)을 추출합니다.

## 📂 프로젝트 구조

```
.
├── Dockerfile
├── docker-compose.yml
├── package.json
├── .env                # 환경 변수 설정
├── public/             # 정적 파일 (CSS, 업로드된 이미지)
├── server.js           # 메인 서버 로직 (취약점 구현 포함)
├── verify_attacks_v2.js # 취약점 검증 스크립트
├── verify_admin.js      # 관리자 기능 검증 스크립트
└── views/              # EJS 템플릿 (프론트엔드)
```