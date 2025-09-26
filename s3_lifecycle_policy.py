import boto3
import logging
import os

# Setup logging (remains the same)
logging.basicConfig(filename='logs/lifecycle_logs.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

def get_s3_client(access_key, secret_key, region):
    """Initializes and returns an S3 client using user-provided credentials."""
    return boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )

def create_s3_bucket(s3, bucket_name, region):
    """Creates a new S3 bucket."""
    try:
        # Note: LocationConstraint is only needed for regions other than us-east-1
        if region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        message = f"✅ Success: Bucket '{bucket_name}' created in {region}."
        logging.info(message)
        return {"status": "success", "message": message}
    except Exception as e:
        message = f"❌ Error creating bucket '{bucket_name}': {e}"
        logging.error(message)
        return {"status": "error", "message": message}


def upload_sample_file(s3, bucket_name, key, content="Sample data for S3 optimization project."):
    """Uploads a simple text file to the bucket for testing policy transitions."""
    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body=content.encode('utf-8'))
        message = f"✅ Success: Sample file '{key}' uploaded to '{bucket_name}'."
        logging.info(message)
        return {"status": "success", "message": message}
    except Exception as e:
        message = f"❌ Error uploading file '{key}': {e}"
        logging.error(message)
        return {"status": "error", "message": message}


def apply_lifecycle_policy(s3, bucket_name, glacier_days, deep_archive_days, expiration_days):
    """Applies a customized lifecycle policy."""
    try:
        glacier_days = int(glacier_days)
        deep_archive_days = int(deep_archive_days)
        expiration_days = int(expiration_days)
    except ValueError:
        return {"status": "error", "message": "Policy days must be valid integers."}

    lifecycle_configuration = {
        'Rules': [
            {
                'ID': 'CustomArchivalPolicy',
                'Status': 'Enabled',
                'Prefix': 'archive/', # Apply policy to objects with this prefix (best practice)
                'Transitions': [
                    {
                        'Days': glacier_days,
                        'StorageClass': 'GLACIER'
                    },
                    {
                        'Days': deep_archive_days,
                        'StorageClass': 'GLACIER_DEEP_ARCHIVE'
                    }
                ],
                'Expiration': {
                    'Days': expiration_days
                },
            },
        ]
    }

    try:
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_configuration
        )
        message = (f"✅ Success: Custom lifecycle policy applied to {bucket_name}. "
                   f"Transitions: Glacier@{glacier_days} days, DeepArchive@{deep_archive_days} days. Expiration: {expiration_days} days.")
        logging.info(message)
        return {"status": "success", "message": message}
    except Exception as e:
        message = f"❌ Error applying lifecycle policy: {e}"
        logging.error(message)
        return {"status": "error", "message": message}