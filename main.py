from rembg import remove
import boto3
from kafka import KafkaConsumer, KafkaProducer
import configparser as parser
import json
from json import dumps

properties = parser.ConfigParser()
properties.read('./config.ini')
aws_config = properties['AWS']
aws_access_key_id = aws_config['aws_access_key_id']
aws_secret_access_key = aws_config['aws_secret_access_key']
s3_bucket = aws_config['s3_bucket']
kafka_config = properties['Kafka']
bootstrap_servers = kafka_config['bootstrap_servers']
sasl_plain_username = kafka_config['sasl_plain_username']
sasl_plain_password = kafka_config['sasl_plain_password']


def s3_connection():
    try:
        s3 = boto3.client(
            service_name="s3",
            region_name="ap-northeast-2",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
    except Exception as e:
        print(e)
    else:
        print("s3 bucket connected!")
        return s3


s3 = s3_connection()


def image_convert(origin_key):
    image_bytes = s3.get_object(Bucket=s3_bucket, Key=origin_key)["Body"].read()
    image_key = origin_key.split('/')[1]
    s3.put_object(Bucket=s3_bucket, Key="mask/" + image_key, Body=remove(image_bytes, only_mask=True))
    return image_key


# 카프카 컨슈머 설정
consumer = KafkaConsumer(
    bootstrap_servers=[bootstrap_servers],
    sasl_mechanism='SCRAM-SHA-256',
    security_protocol='SASL_SSL',
    sasl_plain_username=sasl_plain_username,
    sasl_plain_password=sasl_plain_password,
    group_id='testgroup',
    auto_offset_reset='earliest',
)
consumer.subscribe(['originImage'])
producer = KafkaProducer(
    bootstrap_servers=[bootstrap_servers],
    sasl_mechanism='SCRAM-SHA-256',
    security_protocol='SASL_SSL',
    sasl_plain_username=sasl_plain_username,
    sasl_plain_password=sasl_plain_password,
    value_serializer=lambda x: dumps(x).encode('utf-8')

)

# 카프카 메시지 처리
for message in consumer:
    message = message.value.decode('utf-8')
    producer.send('maskImage', value=json.dumps({"image_key": image_convert(json.loads(message).pop('userMail'))}))

producer.close()
consumer.close()
