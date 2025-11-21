import boto3
import os
from PIL import Image
import io

s3 = boto3.client('s3')

def lambda_handler(event, context):
    source_bucket = event["sourceBucket"]
    image_key = event["imageKey"]
    dest_bucket = os.environ.get("DEST_BUCKET")  # From environment variable

    # Download image from S3
    tmp_path = f"/tmp/{image_key}"
    s3.download_file(source_bucket, image_key, tmp_path)

    # Resize the image
    img = Image.open(tmp_path)
    img = img.resize((300, 300))
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)

    # Upload resized image back to S3
    output_key = f"resized-{image_key}"
    s3.put_object(Bucket=dest_bucket, Key=output_key, Body=buffer)

    return {
        "message": "Image resized successfully!",
        "output_key": output_key
    }
