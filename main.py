from rembg import remove
import boto3
from kafka import KafkaConsumer, KafkaProducer
import configparser as parser
import json
from json import dumps
import time
from google.cloud import storage

properties = parser.ConfigParser()
properties.read('./config/config.ini')
aws_config = properties['AWS']
aws_access_key_id = aws_config['aws_access_key_id']
aws_secret_access_key = aws_config['aws_secret_access_key']
s3_bucket = aws_config['s3_bucket']
kafka_config = properties['Kafka']
bootstrap_servers = kafka_config['bootstrap_servers']
sasl_plain_username = kafka_config['sasl_plain_username']
sasl_plain_password = kafka_config['sasl_plain_password']
gcp_config = properties['gcp']
project_id = gcp_config['project_id']
gcs_bucket = gcp_config['gcs_bucket']


def gcs_connection():
    client = storage.Client(project=project_id)
    return client


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


# s3 = s3_connection()
bucket = gcs_connection().bucket(gcs_bucket)


def image_convert(origin_key, mail):
    now = time.time()
    now = int(now)
    now = str(now)

    image_bytes = s3.get_object(Bucket=s3_bucket, Key=origin_key)["Body"].read()
    image_key = (origin_key.split('/')[1]).split('.')[0] + mail + now + ".png"
    s3.put_object(Bucket=s3_bucket, Key="mask/" + image_key, Body=remove(image_bytes, only_mask=True))
    print("Converted and put Success. User : " + mail)
    return image_key


def image_convert_gcs(origin_key, mail):
    now = time.time()
    now = int(now)
    now = str(now)

    image_bytes = bucket.blob(origin_key).download_as_string()
    image_key = (origin_key.split('/')[1]).split('.')[0] + mail + now + ".png"
    blob = bucket.blob(image_key)
    blob.upload_from_string(remove(image_bytes, only_mask=True))
    print("Converted and put Success. User : " + mail)
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
    user_mail = json.loads(message).pop('user_mail')
    producer.send('maskImage', value=json.dumps({"prompt": json.loads(message).pop('prompt'),
                                                 "mask_key": image_convert_gcs(json.loads(message).pop('origin_key'),
                                                                               user_mail),
                                                 "user_mail": user_mail,
                                                 "origin_key": json.loads(message).pop('origin_key')
                                                 }))

producer.close()
consumer.close()
