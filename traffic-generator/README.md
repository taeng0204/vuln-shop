# Normal Traffic Generator

NIDS(네트워크 침입 탐지 시스템) 학습을 위한 **정상 트래픽 생성기**입니다.
다양한 사용자 페르소나와 현실적인 행동 패턴을 시뮬레이션합니다.

## 🚀 실행 방법

```bash
cd traffic-generator
uv run main.py
```

환경변수로 설정 가능:
```bash
TARGET_URL=http://192.168.1.10:3000 DURATION=1800 MAX_USERS=30 uv run main.py
```

## 🎭 사용자 페르소나

| 페르소나 | 비율 | 행동 패턴 |
|---------|------|----------|
| **visitor** | 20% | 브라우징만, 로그인 안함 |
| **new_user** | 30% | 회원가입 → 로그인 → 활동 |
| **returning** | 25% | 기존 계정 로그인 (실패 가능) |
| **active** | 15% | 많은 글쓰기, 프로필 수정 |
| **order_checker** | 10% | 주문 내역 조회 |

## 🎯 시뮬레이션 기능

### 성공 시나리오
- 회원가입 → 로그인 → 브라우징
- 게시글 작성
- 프로필 페이지 조회
- 주문 내역 조회
- 로그아웃 → 재로그인

### 실패 시나리오
- **로그인 실패** (30%): 잘못된 비밀번호
- **가입 실패** (20%): 중복 username
- **오타 발생** (10%): 입력값 typo

### User-Agent 다양성
10개의 다른 브라우저/디바이스 User-Agent:
- Chrome, Firefox, Safari, Edge (Desktop)
- iPhone, Android (Mobile)
- iPad (Tablet)
- Googlebot (Bot)

## ⚙️ 설정 (config.py)

| 설정 | 기본값 | 설명 |
|-----|-------|------|
| `TARGET_URL` | localhost:3000 | 대상 서버 |
| `DURATION` | 3600 | 실행 시간 (초) |
| `MAX_USERS` | 50 | 동시 사용자 수 |
| `LOGIN_FAIL_RATE` | 0.30 | 로그인 실패 확률 |
| `SIGNUP_DUPLICATE_RATE` | 0.20 | 가입 실패 확률 |

## 📊 출력 예시

```
============================================================
Traffic Generator - NIDS Normal Traffic Simulator
============================================================
Target: http://localhost:3000
Duration: 1800 seconds (30.0 minutes)
Max Concurrent Users: 50
User-Agent Pool: 10 variants
============================================================

[User 1] Started as 'new_user'
[new_user:john_doe] Behavior: New User (signup → explore)
[new_user:john_doe] Browsing home page...
[new_user:john_doe] Attempting registration as 'john_doe'...
...

============================================================
Traffic Generation Complete!
============================================================
Total Users Spawned: 150
Completed Sessions: 148

Persona Distribution:
  active: 22 (14.7%)
  new_user: 45 (30.0%)
  order_checker: 15 (10.0%)
  returning: 38 (25.3%)
  visitor: 30 (20.0%)
============================================================
```
