import os
import asyncio
import aioboto3
from botocore.exceptions import BotoCoreError, ClientError

AWS_ACCESS_KEY_ID = 'your-access-key-id'
AWS_SECRET_ACCESS_KEY = 'your-secret-access-key'
AWS_REGION = 'your-region'
S3_BUCKET_NAME = 'your-bucket-name'
CHUNK_SIZE = 8 * 1024 * 1024  # 每个分块的大小，建议为8MB


async def upload_part(s3_client, bucket_name, key, upload_id, part_number, data):
    try:
        response = await s3_client.upload_part(
            Bucket=bucket_name,
            Key=key,
            UploadId=upload_id,
            PartNumber=part_number,
            Body=data
        )
        return {'PartNumber': part_number, 'ETag': response['ETag']}
    except (BotoCoreError, ClientError) as e:
        print(f"分块 {part_number} 上传失败: {e}")
        raise

async def multipart_upload(file_path, bucket_name, key):
    session = aioboto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    file_size = os.path.getsize(file_path)
    uploaded_bytes = 0

    async with session.client('s3') as s3_client:
        try:
            # 初始化分块上传
            response = await s3_client.create_multipart_upload(Bucket=bucket_name, Key=key)
            upload_id = response['UploadId']

            tasks = []
            parts = []
            part_number = 1

            # 读取文件并分块上传
            with open(file_path, 'rb') as file:
                while True:
                    data = file.read(CHUNK_SIZE)
                    if not data:
                        break
                    task = asyncio.create_task(
                        upload_part(s3_client, bucket_name, key, upload_id, part_number, data)
                    )
                    tasks.append(task)
                    part_number += 1
                    uploaded_bytes += len(data)
                    progress = (uploaded_bytes / file_size) * 100
                    print(f"上传进度: {progress:.2f}%")

            # 等待所有分块上传完成
            for task in asyncio.as_completed(tasks):
                part = await task
                parts.append(part)

            # 按 PartNumber 排序
            parts.sort(key=lambda x: x['PartNumber'])

            # 完成分块上传
            await s3_client.complete_multipart_upload(
                Bucket=bucket_name,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            print(f"文件 {file_path} 上传成功。")

        except (BotoCoreError, ClientError) as e:
            print(f"上传失败: {e}")
            # 如果发生错误，尝试中止分块上传
            await s3_client.abort_multipart_upload(Bucket=bucket_name, Key=key, UploadId=upload_id)
            raise