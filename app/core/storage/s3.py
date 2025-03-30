import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings

UNEXPECTED_ERROR_MESSAGE = "An unexpected error occurred"


class StorageClient:

    def __init__(self):
        self.s3_session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.endpoint_url = settings.AWS_S3_ENDPOINT_URL

    async def __aenter__(self):
        """异步上下文管理，创建 S3 客户端"""
        self.s3_client = await self.s3_session.client(
            "s3", endpoint_url=self.endpoint_url
        ).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.s3_client.__aexit__(exc_type, exc_val, exc_tb)

    async def ensure_bucket_exists(self, bucket_name: str):
        """确保 S3 存储桶存在"""
        try:
            await self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError:
            await self.s3_client.create_bucket(Bucket=bucket_name)

    async def upload_chunk(
        self, bucket_name, remote_path, file_chunk, part_num, upload_id=None, parts=None
    ):
        
        parts = parts or []
        self.ensure_bucket_exists(bucket_name=bucket_name)

        try:
            if upload_id is None:
                response = await self.s3_client.create_multipart_upload(
                    Bucket=bucket_name, Key=remote_path
                )
                upload_id = response["UploadID"]

            response = await self.s3_client.upload_part(
                Bucket=bucket_name,
                Key=remote_path,
                PartNumber=part_num,
                UploadId=upload_id,
                Body=file_chunk,
            )
            parts.append({"PartNumber": part_num, "ETag": response["ETag"]})
            return upload_id, parts
        
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "403":
                raise ValueError(f"Access denied: {e}")
            else:
                raise ValueError(f"Unexpected error: {e}")
        except NoCredentialsError as e:
            raise ClientError(f"Unable to locate credentials: {e}")
        except Exception as e:
            return f"{UNEXPECTED_ERROR_MESSAGE}: {str(e)}"
        
    async def complete_upload(self, bucket_name, remote_path, upload_id, parts):
        try:
            await self.s3_client.complete_multipart_upload(
                Bucket=bucket_name,
                Key=remote_path,
                UploadId=upload_id,
                MultipartUpload={"Parts": sorted(parts, key=lambda x: x["PartNumber"])},
            )
            return remote_path
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "403":
                raise ValueError(f"Access denied: {e}")
            else:
                raise ValueError(f"Unexpected error: {e}")
        except NoCredentialsError as e:
            raise ClientError(f"Unable to locate credentials: {e}")
        except Exception as e:
            raise ClientError(f"{UNEXPECTED_ERROR_MESSAGE}: {str(e)}")

    async def abort_upload(self, bucket_name, remote_path, upload_id):
        try:
            await self.s3_client.abort_multipart_upload(
                Bucket=bucket_name, 
                Key=remote_path, 
                UploadId=upload_id
            )
            return f"{bucket_name}/{remote_path}"
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "403":
                raise ValueError(f"Access denied: {e}")
            else:
                raise ValueError(f"Unexpected error: {e}")
        except NoCredentialsError as e:
            raise ClientError(f"Unable to locate credentials: {e}")
        except Exception as e:
            raise ClientError(f"{UNEXPECTED_ERROR_MESSAGE}: {str(e)}")

    async def stat_object(self, bucket_name, remote_path):
        try:
            response = await self.s3_client.head_object(Bucket=bucket_name, Key=remote_path)
            return response
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "403":
                raise ValueError(f"Access denied: {e}")
            else:
                raise ValueError(f"Unexpected error: {e}")
        except NoCredentialsError as e:
            raise ClientError(f"Unable to locate credentials: {e}")
        except Exception as e:
            raise ClientError(f"{UNEXPECTED_ERROR_MESSAGE}: {str(e)}")
    
    def _parse_path(self, remote_path):
        parts = remote_path.split("/", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            raise ValueError(
                """
                Invalid remote path format.
                Expected format 'bucket-name/path/file'
            """
            )

    async def get_object(self, bucket_name, remote_path, transferred_bytes=0):
        range_param = 'bytes={}-'.format(transferred_bytes)
        try:
            return await self.s3_client.get_object(Bucket=bucket_name, Key=remote_path, Range=range_param)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "403":
                raise ValueError(f"Access denied: {e}")
            else:
                raise ValueError(f"Unexpected error: {e}")
        except NoCredentialsError as e:
            raise ClientError(f"Unable to locate credentials: {e}")
        except Exception as e:
            raise ClientError(f"{UNEXPECTED_ERROR_MESSAGE}: {str(e)}")