# 취약한 스트릿웨어 쇼핑몰 (VULN SHOP) - 구현 계획

## 목표
"VULN SHOP" 브랜드 감성의 세련된 디자인을 갖춘 쇼핑몰을 구축하고, 보안 수준별(v1, v2, v3)로 취약점을 단계적으로 구현하여 교육 및 연구용으로 활용합니다.

## 기술 스택
- **런타임:** Node.js
- **웹 프레임워크:** Express.js
- **데이터베이스:** SQLite3
- **프론트엔드:** EJS, Vanilla CSS (VULN SHOP Design)
- **인프라:** Docker, Docker Compose

## 아키텍처: 환경 변수 기반 보안 레벨
보안 레벨은 애플리케이션 시작 시 **환경 변수 (`SECURITY_LEVEL`)**를 통해 결정됩니다.
UI에서의 변경은 불가능하며, Docker 컨테이너 실행 시 주입된 값에 따라 고정된 보안 정책이 적용됩니다.

- **환경 변수:** `SECURITY_LEVEL=v1` (Default), `v2`, `v3`
- **서버 로직:** `process.env.SECURITY_LEVEL`을 읽어 미들웨어에서 전역 설정.

## 취약점 구현 전략

### 1. SQL Injection (로그인)
- **v1:** 문자열 연결 (`"SELECT ... '" + user + "'"`)
- **v2:** 블랙리스트 필터링 (예: `'`나 `--` 제거) -> 우회 가능.
- **v3:** Prepared Statements (`db.get("SELECT ... ?", [user])`)

### 2. Cross-Site Scripting (XSS) (게시판)
- **v1:** 필터링 없음 (`<%- content %>`)
- **v2:** 단순 문자열 치환 (`<script>` 태그만 제거) -> `<img onerror>` 등으로 우회 가능.
- **v3:** HTML Entity Encoding (`<%= content %>`) 또는 라이브러리 사용.

### 3. [NEW] File Upload (프로필 이미지)
- **v1:** 확장자/타입 검사 없음. 웹쉘 업로드 가능.
- **v2:** 클라이언트 사이드 확장자 검사 또는 `Content-Type` 헤더만 검사.
- **v3:** 서버 사이드 파일 시그니처(Magic Number) 검사 및 파일명 난수화.

### 4. [NEW] IDOR (주문 내역 조회)
- **v1:** `/order?id=1` 요청 시 소유자 검증 없이 조회 가능.
- **v2:** ID를 Base64로 인코딩하여 노출 (`/order?id=MQ==`) -> 디코딩하여 변조 가능.
- **v3:** 세션의 사용자 ID와 주문의 소유자 ID 일치 여부 검증.



## 구현 단계
1.  **프로젝트 구조 개편:** v1/v2/v3 로직 분리.
2.  **새로운 취약점 구현:** 파일 업로드, IDOR.
3.  **디자인 리뉴얼:** VULN SHOP 스타일 적용.
4.  **Docker 패키징:** Dockerfile 및 Compose 작성.
5.  **검증:** 레벨별 취약점 동작 확인.
