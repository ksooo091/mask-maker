# Mask Maker

**클라우드 저장소(S3, GCS)에 저장된 이미지를 가져와 배경제거 후 업로드 **

## 확인사항

1. 사용할 저장소를 정해서 알맞게 코드 수정 필요. 사용하지 않는 저장소는 주석처리 후 사용
2. config.ini 는 프토젝트 루트의 config 디렉토리에 생성

## config.ini 예시
```
[AWS]
aws_access_key_id = 
aws_secret_access_key = 
s3_bucket =
[Kafka]
bootstrap_servers = 
sasl_plain_username = 
sasl_plain_password =
[gcp]
project_id =
gcs_bucket =
```
