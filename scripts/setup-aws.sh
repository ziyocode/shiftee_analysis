#!/bin/bash
# AWS CLI + SAM CLI 설치 가이드 (macOS)
set -euo pipefail

echo "=========================================="
echo " AWS 개발 도구 설치 가이드"
echo "=========================================="

# Homebrew 확인
if ! command -v brew &> /dev/null; then
    echo "Homebrew가 설치되어 있지 않습니다."
    echo "설치: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo ""
echo "1. AWS CLI 설치/업데이트"
if command -v aws &> /dev/null; then
    echo "   이미 설치됨: $(aws --version)"
else
    echo "   설치 중..."
    brew install awscli
fi

echo ""
echo "2. SAM CLI 설치/업데이트"
if command -v sam &> /dev/null; then
    echo "   이미 설치됨: $(sam --version)"
else
    echo "   설치 중..."
    brew install aws-sam-cli
fi

echo ""
echo "3. Docker 확인"
if command -v docker &> /dev/null; then
    echo "   이미 설치됨: $(docker --version)"
else
    echo "   Docker Desktop이 필요합니다."
    echo "   설치: brew install --cask docker"
fi

echo ""
echo "=========================================="
echo " AWS 자격증명 설정"
echo "=========================================="
echo ""
echo "아직 설정하지 않았다면 다음 명령을 실행하세요:"
echo ""
echo "  aws configure"
echo ""
echo "  - AWS Access Key ID: <YOUR_ACCESS_KEY>"
echo "  - AWS Secret Access Key: <YOUR_SECRET_KEY>"
echo "  - Default region: ap-northeast-2"
echo "  - Default output format: json"
echo ""

# 현재 설정 확인
if aws sts get-caller-identity &> /dev/null; then
    echo "현재 AWS 자격증명:"
    aws sts get-caller-identity
else
    echo "AWS 자격증명이 설정되지 않았습니다. 'aws configure'를 실행하세요."
fi
