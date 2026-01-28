# aws-functions

- ec2-hostname-tag.sh : ec2 hostname을 tag의 Name 항목으로 변경
  - 사전 설정 필요사항: 테라폼에서 아래 항목 추가 필요 (instance_metadata_tags enabled)

```hcl
  metadata_options {
    http_endpoint          = "enabled"
    http_tokens            = "required"
    instance_metadata_tags = "enabled"
  }
```
