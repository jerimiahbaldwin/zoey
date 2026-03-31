import boto3
from botocore.exceptions import ClientError

from zoey.config import BUCKET


class S3Store:
    def __init__(self, bucket=BUCKET, client=None):
        self.bucket = bucket
        self.client = client or boto3.client("s3")

    def list_files(self, prefix, limit):
        keys = []
        continuation_token = None

        while len(keys) < limit:
            max_keys = min(1000, limit - len(keys))
            kwargs = {
                "Bucket": self.bucket,
                "Prefix": prefix,
                "MaxKeys": max_keys,
            }
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            result = self.client.list_objects_v2(**kwargs)
            for item in result.get("Contents", []):
                keys.append(item["Key"])

            if not result.get("IsTruncated"):
                break

            continuation_token = result.get("NextContinuationToken")

        return keys

    def read_text(self, key):
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read().decode("utf-8")

    def write_text(self, key, content):
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content.encode("utf-8"))

    def is_missing_key_error(self, error):
        if not isinstance(error, ClientError):
            return False

        code = error.response.get("Error", {}).get("Code", "Unknown")
        return code in {"NoSuchKey", "404"}
