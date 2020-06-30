import datetime
import boto3
import botocore
import os
from smart_open import smart_open
import decimal

from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
stats = dynamodb.Table(os.environ['STATS_TABLE'])
s3_client = boto3.client('s3')

def index(str):
  return True

def handler(event, context):
    src_bucket_name=event['Records'][0]['s3']['bucket']['name']
    file = event['Records'][0]['s3']['object']['key']
    path = 'raw/'
    total_cdr = 0
    file_size = event['Records'][0]['s3']['object']['size']

    for line_encoded in smart_open('s3://'+src_bucket_name+'/'+file, 'rb'):
      line = line_encoded.decode('utf-8')
      index(line)
      if line.startswith("118,1:"):
          date = str(line.split(':')[1]).strip()
          total_cdr = total_cdr + 1
          new_file = datetime.datetime.strptime(date, '%Y%m%d%H%M%S')
          path = str(new_file.year)+'/'+  str(new_file.month)+'/'+  str(new_file.day)+'/'+  str(new_file.hour)+'/' 
    new_path=str(path+file).strip()
    
    copy_source = {
      'Bucket': src_bucket_name,
      'Key': file
    }

    s3_client.copy_object(
      Bucket=os.environ['CDR_BUCKET'],
      CopySource=copy_source,
      Key=new_path
    )

    s3_client.delete_object(
      Bucket=src_bucket_name,
      Key=file
    )

    stats.update_item(
       Key={'id': datetime.date.today().strftime("%Y-%m-%d") },
       ReturnValues="UPDATED_NEW",
       UpdateExpression="ADD total_cdr :val, total_files :val2, size :val3",
       ExpressionAttributeValues={
           ':val': decimal.Decimal(total_cdr),
           ':val2': decimal.Decimal(1),
           ':val3': decimal.Decimal(file_size)
       }
    )
    stats.update_item(
       Key={'id': 'global' },
       ReturnValues="UPDATED_NEW",
       UpdateExpression="ADD total_cdr :val, total_files :val2, size :val3",
       ExpressionAttributeValues={
           ':val': decimal.Decimal(total_cdr),
           ':val2': decimal.Decimal(1),
           ':val3': decimal.Decimal(file_size)
       }
    )

if __name__ == "__main__":
    handler('', '')