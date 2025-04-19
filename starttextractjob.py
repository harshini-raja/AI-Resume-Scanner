import json
import boto3
import os

# AWS Clients
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')
sns_client = boto3.client('sns')

# Environment Variables (Set in Lambda Console)
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '') #process-textract-results       # SNS Topic for Textract completion
ROLE_ARN = os.environ.get('ROLE_ARN', '')#iam role resume-ai-scanner arn
CUSTOM_SNS_TOPIC_ARN = os.environ.get('CUSTOM_SNS_TOPIC_ARN', '')  # New custom topic for custom messages-custom details

def lambda_handler(event, context):
    """
    Starts AWS Textract TEXT DETECTION job (full text extraction).
    Receives a simple SNS message with fileKey, jobDescription, etc.
    """

    print("Received event:", json.dumps(event, indent=2))  # Log the incoming event

    try:
        # 1. Extract the SNS message from the event
        sns_record = event['Records'][0]['Sns']
        message = json.loads(sns_record['Message'])
        print("Parsed SNS message:", json.dumps(message, indent=2))

        # 2. Get fileKey, jobDescription, and (optionally) the bucket name
        file_name = message.get('fileKey')
        job_description = message.get('jobDescription', '').strip()
        
        # If your resume is always in the same bucket, you can hardcode here:
        bucket_name = "job-resume-upload-bucket"
        # If the bucket name varies, pass it in the message or handle it accordingly.

        if not file_name:
            print("Missing fileKey in SNS message.")
            return {'statusCode': 400, 'body': json.dumps("Missing fileKey")}

        print(f"Starting Textract Text Detection job for file: {file_name} from bucket: {bucket_name}")
        print(f"NotificationChannel Setup: SNS_TOPIC_ARN={SNS_TOPIC_ARN}, ROLE_ARN={ROLE_ARN}")

        # 3. Start Textract Text Detection Job (FULL TEXT extraction)
        response = textract_client.start_document_text_detection(
            DocumentLocation={'S3Object': {'Bucket': bucket_name, 'Name': file_name}},
            NotificationChannel={'SNSTopicArn': SNS_TOPIC_ARN, 'RoleArn': ROLE_ARN}
        )

        job_id = response.get('JobId', 'No JobId returned')
        print(f"Textract Text Detection Job Started. Job ID: {job_id}")
        print(f"Full Textract response: {json.dumps(response, indent=2)}")

        # 4. Publish a custom message to the new SNS topic (CUSTOM_SNS_TOPIC_ARN)
        sns_client.publish(
            TopicArn=CUSTOM_SNS_TOPIC_ARN,
            Message=json.dumps({
                'fileKey': file_name,
                'jobDescription': job_description,
                'jobId': job_id
            })
        )
        print("Published custom message with jobId, fileKey, and jobDescription.")

        # 5. (Optional) Store the job description in an S3 bucket
        if job_description:
            print(f"Storing job description to S3: {job_description}")
            s3_client.put_object(
                Bucket="job-descriptions-1",
                Key=f"{file_name}_job_description.txt",
                Body=job_description
            )

        return {
            'statusCode': 200,
            'body': json.dumps(f"Started Textract Text Detection job {job_id} for {file_name}")
        }

    except Exception as e:
        print(f"Error starting Textract job: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error starting Textract job: {str(e)}")
        }
