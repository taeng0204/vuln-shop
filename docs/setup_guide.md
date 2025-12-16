# NIDS 데이터 수집 환경 구축 가이드

## 개요
노트북에서 vuln-shop 서버를 실행하고, Kali Linux VM에서 AI Agent를 활용한 공격을 수행하여 NIDS 학습용 데이터를 수집합니다.

## 아키텍처
```
┌─────────────────────┐          ┌─────────────────────┐
│   노트북 (서버)       │          │   Kali Linux VM      │
│   vuln-shop Docker  │◀─────────│   AI Agent 공격      │
│   + 데이터 수집       │  Network │   (3개 Agent)        │
└─────────────────────┘          └─────────────────────┘
```

## 사전 요구사항

**노트북 (서버):**
- Docker Desktop 설치
- Python 3.9+ (uv 패키지 매니저 권장)

**Kali Linux VM:**
- 노트북과 같은 네트워크 (NAT 또는 브릿지 모드)
- curl, Python 설치됨

---

## 1단계: 서버 실행 (노트북)

```bash
cd vuln-shop
docker compose up -d --build
```

**노트북 IP 확인:**
```bash
# macOS
ipconfig getifaddr en0   # 예: 192.168.0.10
```

**서버 확인:**
```bash
curl http://localhost:3000/
# HTML 응답이 오면 성공
```

---

## 2단계: 정상 트래픽 생성 (노트북 - 터미널 2)

> [!NOTE]
> 적절한 양의 정상 트래픽을 생성하기 위한 설정입니다.
> - 동시 사용자: 50명 (기본값)
> - 딜레이: 0.1~1.0초 (적절한 요청 간격)
> - 페르소나별 다양한 행동 패턴 적용

```bash
cd traffic-generator
SIMULATED_IP=192.168.0.200 DURATION=1800 uv run main.py
```

**옵션 조정 (필요시):**
```bash
# 트래픽 양 조절
MAX_USERS=100 SIMULATED_IP=192.168.0.200 DURATION=1800 uv run main.py
```

---

## 3단계: AI Agent 공격 수행 (Kali Linux VM)

각 AI Agent에게 `docs/ai_agent_attack_guide.md` 문서를 제공하고 공격을 수행합니다.

**타겟 URL**: `http://{노트북IP}:3000` (예: `http://192.168.0.10:3000`)

**Agent별 IP:**
Kali에서 실제 IP가 사용되지만, X-Forwarded-For로 구분 가능:
| Agent | X-Forwarded-For |
|-------|----------------|
| Agent 1 | 10.0.0.101 |
| Agent 2 | 10.0.0.102 |
| Agent 3 | 10.0.0.103 |

---

## 4단계: 데이터 수집 (노트북 - 30분 후)

```bash
python scripts/merge_logs.py \
    --attacker-ip "10.0.0.101,10.0.0.102,10.0.0.103" \
    --normal-ip "192.168.0.200" \
    --output ./output/nids_dataset.csv
```

---

## 5단계: 결과 확인

```bash
python3 -c "
import csv
from collections import Counter
rows = list(csv.DictReader(open('output/nids_dataset.csv')))
labels = Counter(r['label'] for r in rows)
print('Label Distribution:')
for label, count in sorted(labels.items()):
    print(f'  {label}: {count} ({100*count/len(rows):.1f}%)')
"
```

---

## 폴더 구조

```
output/
├── nids_dataset.csv     # 최종 라벨링된 데이터셋
logs/
├── traffic-*.log        # L7 애플리케이션 로그
csv/
├── *.csv                # L3/4 패킷 플로우 데이터
```

---

## 환경 정리

```bash
docker compose down
rm -f logs/*.log csv/*.csv
```
