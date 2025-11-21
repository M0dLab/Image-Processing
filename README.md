

## How to Run the Application

### **1️⃣ Create Two S3 Buckets**

| Purpose                     | Bucket Name                |
| --------------------------- | -------------------------- |
| Upload original images here | `emmanuel-original-images` |
| Resized images appear here  | `emmanuel-resized-images`  |

Upload a test image: `emmanuel.png`

---

### **2️⃣ Create Lambda Function**

**Name:** `resize-image-lambda`
**Runtime:** Python 3.12
**Handler:** `lambda_function.lambda_handler`

#### Paste this code:

```python
import boto3
import os
from PIL import Image
import io

s3 = boto3.client('s3')

def lambda_handler(event, context):
    source_bucket = event["sourceBucket"]
    image_key = event["imageKey"]
    dest_bucket = os.environ.get("DEST_BUCKET")

    tmp_path = f"/tmp/{image_key}"
    s3.download_file(source_bucket, image_key, tmp_path)

    img = Image.open(tmp_path)
    img = img.resize((300, 300))
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)

    output_key = f"resized-{image_key}"
    s3.put_object(Bucket=dest_bucket, Key=output_key, Body=buffer)

    return {"message": "Image resized successfully!", "output_key": output_key}
```

#### Environment Variable:

| Key           | Value                     |
| ------------- | ------------------------- |
| `DEST_BUCKET` | `emmanuel-resized-images` |

---

### **3️⃣ Add Pillow Layer**

Open **CloudShell** and run:

```
mkdir pillow_layer
cd pillow_layer
pip install pillow -t python/
zip -r pillow_layer.zip python
```

Then in Lambda:

```
Layers → Create Layer → Upload pillow_layer.zip
Runtime: Python 3.12
Attach to your Lambda function
```

---

### **4️⃣ IAM Permissions**

Go to **IAM → Roles → Select Lambda Role → Add inline policy**

Paste this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:HeadObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::emmanuel-original-images",
        "arn:aws:s3:::emmanuel-original-images/*"
      ]
    }
  ]
}
```

---

### **5️⃣ Create Step Functions**

**Name:** `ImageProcessingStateMachine`

Paste this definition:

```json
{
  "Comment": "Image Processing Workflow",
  "StartAt": "ResizeImage",
  "States": {
    "ResizeImage": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:424926559699:function:resize-image-lambda",
      "ResultPath": "$.result",
      "Next": "CheckResult"
    },
    "CheckResult": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.result.message",
          "StringEquals": "Image resized successfully!",
          "Next": "SuccessState"
        }
      ],
      "Default": "FailState"
    },
    "SuccessState": { "Type": "Succeed" },
    "FailState": { "Type": "Fail" }
  }
}
```

---

### **6️⃣ Create API Gateway**

1. Create **REST API**
2. Create **resource** `/resize`
3. Add **POST** method
4. Integration Type → **Step Functions – StartExecution**
5. Select your state machine

#### **Mapping Template** (`application/json`)

```json
{
  "stateMachineArn": "arn:aws:states:us-east-1:424926559699:stateMachine:ImageProcessingStateMachine",
  "input": "$util.escapeJavaScript($input.body)"
}
```

Deploy API → Create stage → Name it `dev`

---

### **7️⃣ Test with Postman**

**Method:** `POST`
**URL:**

```
https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/resize
```

#### **Body (JSON)**

```json
{
  "sourceBucket": "emmanuel-original-images",
  "imageKey": "emmanuel.png"
}
```

**Success Response:**

```json
{
  "message": "Image resized successfully!",
  "output_key": "resized-emmanuel.png"
}
```

Check S3 → `emmanuel-resized-images` → file should be there.
