#!/bin/bash
# ECR 푸시 + SAM 배포 원커맨드 스크립트
set -euo pipefail

REGION="${AWS_DEFAULT_REGION:-ap-northeast-2}"
ENVIRONMENT="${1:-prod}"
ECR_REPO_NAME="shiftee-analysis"
STACK_NAME="shiftee-analysis-${ENVIRONMENT}"

echo "=========================================="
echo " Shiftee Analysis 배포"
echo " Environment: ${ENVIRONMENT}"
echo " Region: ${REGION}"
echo "=========================================="

# Docker 데몬 확인
echo "0. Docker 데몬 확인..."
if ! docker info &> /dev/null; then
    echo "   Docker가 실행되고 있지 않습니다."
    echo "   Docker Desktop을 실행한 후 다시 시도하세요."
    echo ""
    echo "   macOS: open -a Docker"
    exit 1
fi
echo "   Docker 실행 중"
echo ""

# AWS 계정 ID 확인
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
echo "AWS Account: ${ACCOUNT_ID}"
echo ""

# 1. ECR 리포지토리 생성 (없으면)
echo "1. ECR 리포지토리 확인/생성..."
if ! aws ecr describe-repositories --repository-names "${ECR_REPO_NAME}" --region "${REGION}" &> /dev/null; then
    echo "   리포지토리 생성 중..."
    aws ecr create-repository \
        --repository-name "${ECR_REPO_NAME}" \
        --image-scanning-configuration scanOnPush=true \
        --region "${REGION}"
    echo "   생성 완료!"
else
    echo "   이미 존재합니다."
fi

# 2. SAM 빌드 (Docker 이미지 빌드 포함)
echo ""
echo "2. SAM 빌드 (Docker 이미지 빌드 포함, 첫 빌드 시 5~10분 소요)..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

cd "${PROJECT_DIR}/infra"
sam build --template-file template.yaml

# 3. SAM 배포 (ECR 푸시 + CloudFormation 배포)
echo ""
echo "3. SAM 배포 (이미지 푸시 + 스택 생성)..."
sam deploy \
    --stack-name "${STACK_NAME}" \
    --capabilities CAPABILITY_IAM \
    --region "${REGION}" \
    --parameter-overrides "Environment=${ENVIRONMENT}" \
    --image-repository "${ECR_URI}/${ECR_REPO_NAME}" \
    --no-confirm-changeset

echo ""
echo "=========================================="
echo " 배포 완료!"
echo "=========================================="
echo ""
echo "확인 방법:"
echo "  aws lambda invoke --function-name shiftee-analysis-${ENVIRONMENT} /tmp/response.json && cat /tmp/response.json"
echo "  aws logs tail /aws/lambda/shiftee-analysis-${ENVIRONMENT} --follow"
echo "  aws s3 ls s3://shiftee-reports-${ENVIRONMENT}/reports/"
