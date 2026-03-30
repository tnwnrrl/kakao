#!/bin/bash
# 와이시티 입주민 인증 챗봇 NAS 배포 스크립트

NAS_HOST="192.168.219.187"
NAS_PORT="55"
NAS_USER="tnwnrrl"
NAS_PATH="/volume1/homes/tnwnrrl/kakao"
LOCAL_PATH="$(cd "$(dirname "$0")" && pwd)"

echo "=== 와이시티 인증봇 NAS 배포 ==="

# 1. tar로 파일 전송 (볼륨 마운트된 app/ + docker-compose.yml)
echo "[1/2] 파일 전송 중..."
tar czf /tmp/kakao_deploy.tar.gz \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  -C "${LOCAL_PATH}" \
  app/ docker-compose.yml

ssh -p ${NAS_PORT} ${NAS_USER}@${NAS_HOST} "cat > /tmp/kakao_deploy.tar.gz" < /tmp/kakao_deploy.tar.gz

if [ $? -ne 0 ]; then
  echo "파일 전송 실패"
  exit 1
fi

ssh -p ${NAS_PORT} ${NAS_USER}@${NAS_HOST} \
  "cd ${NAS_PATH} && tar xzf /tmp/kakao_deploy.tar.gz 2>/dev/null; rm -f /tmp/kakao_deploy.tar.gz"
echo "파일 전송 완료"

# 2. 컨테이너 재시작 (볼륨 마운트 → 파일 복사만으로 코드 반영)
echo "[2/2] 컨테이너 재시작 중..."
ssh -p ${NAS_PORT} -t ${NAS_USER}@${NAS_HOST} \
  "sudo -S /usr/local/bin/docker restart kakao-auth 2>&1" < <(echo "Aksksla12!")

echo ""
echo "배포 완료!"
echo "내부 주소: http://192.168.219.187:8084"
echo "외부 주소: https://kakao.mysterydam.com"
echo "Kakao 스킬 URL: https://kakao.mysterydam.com/webhook"
