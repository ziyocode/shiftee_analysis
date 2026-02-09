#!/bin/bash
# Secrets Manager 초기 시크릿 생성 (일회성)
set -euo pipefail

REGION="${AWS_DEFAULT_REGION:-ap-northeast-2}"

echo "=========================================="
echo " Secrets Manager 시크릿 설정"
echo "=========================================="
echo ""

# 1. Shiftee 자격증명
echo "1. Shiftee 자격증명 (shiftee/credentials)"
read -rp "   SHIFTEE_ID (이메일): " SHIFTEE_ID
read -rsp "   SHIFTEE_PASSWORD: " SHIFTEE_PASSWORD
echo ""

if aws secretsmanager describe-secret --secret-id shiftee/credentials --region "$REGION" &> /dev/null; then
    echo "   시크릿이 이미 존재합니다. 업데이트 중..."
    aws secretsmanager put-secret-value \
        --secret-id shiftee/credentials \
        --secret-string "{\"SHIFTEE_ID\": \"${SHIFTEE_ID}\", \"SHIFTEE_PASSWORD\": \"${SHIFTEE_PASSWORD}\"}" \
        --region "$REGION"
else
    echo "   시크릿 생성 중..."
    aws secretsmanager create-secret \
        --name shiftee/credentials \
        --description "Shiftee login credentials" \
        --secret-string "{\"SHIFTEE_ID\": \"${SHIFTEE_ID}\", \"SHIFTEE_PASSWORD\": \"${SHIFTEE_PASSWORD}\"}" \
        --region "$REGION"
fi
echo "   완료!"

echo ""

# 2. 카카오 토큰 (옵션)
read -rp "2. 카카오톡 토큰도 설정하시겠습니까? (y/N): " SETUP_KAKAO

if [[ "${SETUP_KAKAO}" == "y" ]]; then
    read -rp "   app_key (REST API 키): " KAKAO_APP_KEY
    read -rp "   access_token: " KAKAO_ACCESS_TOKEN
    read -rp "   refresh_token: " KAKAO_REFRESH_TOKEN

    KAKAO_SECRET="{\"app_key\": \"${KAKAO_APP_KEY}\", \"access_token\": \"${KAKAO_ACCESS_TOKEN}\", \"refresh_token\": \"${KAKAO_REFRESH_TOKEN}\"}"

    if aws secretsmanager describe-secret --secret-id shiftee/kakao-token --region "$REGION" &> /dev/null; then
        echo "   시크릿이 이미 존재합니다. 업데이트 중..."
        aws secretsmanager put-secret-value \
            --secret-id shiftee/kakao-token \
            --secret-string "$KAKAO_SECRET" \
            --region "$REGION"
    else
        echo "   시크릿 생성 중..."
        aws secretsmanager create-secret \
            --name shiftee/kakao-token \
            --description "KakaoTalk API tokens for Shiftee notifications" \
            --secret-string "$KAKAO_SECRET" \
            --region "$REGION"
    fi
    echo "   완료!"
fi

echo ""
echo "=========================================="
echo " 설정 완료"
echo "=========================================="
echo ""
echo "생성된 시크릿 확인:"
aws secretsmanager list-secrets \
    --filters Key=name,Values=shiftee \
    --query 'SecretList[].{Name:Name,ARN:ARN}' \
    --output table \
    --region "$REGION"
