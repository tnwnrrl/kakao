#!/bin/bash
# 와이시티 입주민 인증 챗봇 NAS 배포 스크립트

NAS_HOST="tnwnrrl.synology.me"
NAS_PORT="55"
NAS_USER="tnwnrrl"
NAS_PATH="/volume1/homes/tnwnrrl/kakao"
DOCKER_COMPOSE="/volume2/@appstore/Docker/usr/bin/docker-compose"
LOCAL_PATH="$(cd "$(dirname "$0")" && pwd)"

echo "=== 와이시티 인증봇 NAS 배포 ==="

# 1. rsync로 파일 전송 (.env 제외)
echo "[1/2] 파일 전송 중..."
rsync -avz \
  --exclude='.env' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='.playwright-mcp' \
  -e "ssh -p ${NAS_PORT}" \
  "${LOCAL_PATH}/" \
  "${NAS_USER}@${NAS_HOST}:${NAS_PATH}/"

if [ $? -ne 0 ]; then
  echo "파일 전송 실패"
  exit 1
fi

# 2. Docker 컨테이너 빌드 & 실행
echo "[2/2] Docker 컨테이너 빌드 중..."
ssh -p ${NAS_PORT} ${NAS_USER}@${NAS_HOST} \
  "cd ${NAS_PATH} && ${DOCKER_COMPOSE} up -d --build"

if [ $? -eq 0 ]; then
  echo ""
  echo "배포 완료!"
  echo "내부 주소: http://192.168.219.187:8084"
  echo "외부 주소: https://kakao.mysterydam.com"
  echo "Kakao 스킬 URL: https://kakao.mysterydam.com/webhook"
else
  echo "Docker 실행 실패"
  exit 1
fi
