#!/bin/bash

# 1. IMDSv2 토큰 발급
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# 2. Name 태그 조회 (메타데이터 태그)
NAME_TAG=$(curl -s \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  "http://169.254.169.254/latest/meta-data/tags/instance/Name")

# 3. Name 태그 없으면 종료
if [ -z "$NAME_TAG" ] || [ "$NAME_TAG" = "Not Found" ]; then
  echo "IMDS에서 Name 태그를 찾지 못했습니다."
  exit 0
fi

# 4. hostname 변경
hostnamectl set-hostname "$NAME_TAG"

# 5. 확인
echo "hostname이 '$NAME_TAG' 로 변경되었습니다."
hostnamectl
