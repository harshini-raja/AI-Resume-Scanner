import json
import boto3

sns_client = boto3.client('sns')

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-2:329599659950:start-textract-job-after-resume-upload'


def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # Allow all origins or specify your domain
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
    }

    try:
        file_key = event['fileKey']
        job_description = event['jobDescription']
        
        if not file_key or not job_description.strip():
            raise ValueError("Missing fileKey or jobDescription")
        print(f"Received fileKey: {file_key}")
        print(f"Received jobDescription: {job_description}")

        # Prepare SNS message with fileKey and jobDescription
        message = {
            'fileKey': file_key,
            'jobDescription': job_description
        }

        # Publish the message to SNS
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps({'default': json.dumps(message)}),
            MessageStructure='json'
        )
        
        # Return success response with CORS headers
        return {
            'statusCode': 200,
            'headers': headers,  # Include CORS headers in the response
            'body': json.dumps("Job description and file key sent to SNS")
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        
        # Return error response with CORS headers
        return {
            'statusCode': 500,
            'headers': headers,  # Include CORS headers in the response
            'body': json.dumps(f"Error sending data to SNS: {str(e)}")
        }
