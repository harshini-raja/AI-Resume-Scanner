import json
import boto3
import os
import time
import re

# AWS Clients
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')

# Environment Variables
RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET', '')#resume-textract-results arn

def get_textract_results(job_id):
    """Fetch Textract Text Detection results."""
    try:
        status = "IN_PROGRESS"
        retries = 10
        while status == "IN_PROGRESS" and retries > 0:
            response = textract_client.get_document_text_detection(JobId=job_id)
            status = response["JobStatus"]
            print(f"Textract job status: {status}")
            if status == "IN_PROGRESS":
                time.sleep(20)
                retries -= 1

        if status != "SUCCEEDED":
            raise ValueError(f"Textract job failed or incomplete: {status}")

        # Extract LINE blocks (raw text)
        extracted_lines = []
        for block in response.get("Blocks", []):
            if block["BlockType"] == "LINE":
                text_line = block.get("Text", "").strip()
                if text_line:
                    extracted_lines.append(text_line)

        if not extracted_lines:
            raise ValueError("No text lines found in Textract response.")

        print("Extracted Text Lines:", json.dumps(extracted_lines, indent=2))
        return extracted_lines

    except Exception as e:
        print(f"Error retrieving Textract results: {str(e)}")
        raise e

def calculate_match_percentage(extracted_lines, job_requirements):
    """Compare job requirements against raw extracted text lines."""
    combined_text = " ".join(extracted_lines).lower()
    print("Combined Raw Text for Matching:", combined_text)

    matching_skills = set()
    for skill in job_requirements:
        if skill.lower() in combined_text:
            matching_skills.add(skill)

    match_percentage = (len(matching_skills) / len(job_requirements)) * 100 if job_requirements else 0
    return round(match_percentage, 2), matching_skills

def extract_nouns_from_text(job_description):
    """Extracts potential nouns (skills) from the job description text block."""
    # Using a simple regex to capture capitalized words as a heuristic for skills/keywords.
    nouns = re.findall(r'\b[A-Z][a-z]*\b', job_description)
    return set(nouns)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    try:
        # Parse the custom SNS message.
        # This Lambda is now subscribed to the custom SNS topic that includes:
        # - 'jobId' (the Textract Job ID)
        # - 'jobDescription' (provided from the front end)
        # - 'fileKey' (the S3 file key for the uploaded resume)
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        print("Custom SNS Message:", json.dumps(sns_message, indent=2))

        # Retrieve required fields from the custom message.
        job_id = sns_message.get('jobId')
        job_description = sns_message.get('jobDescription', '')
        if not job_id or not job_description:
            raise ValueError("jobId or jobDescription not found in SNS message.")

        print(f"Processing Textract Job ID: {job_id}")

        # Get Textract results using the jobId.
        extracted_lines = get_textract_results(job_id)

        # Extract potential skill keywords (nouns) from the job description.
        extracted_skills_from_description = extract_nouns_from_text(job_description)

        # Calculate match percentage between extracted text and job requirements.
        match_score, matching_skills = calculate_match_percentage(extracted_lines, extracted_skills_from_description)

        # Prepare the final result JSON.
        result_data = {
            "JobId": job_id,
            "ExtractedTextLines": extracted_lines,
            "MatchScore": match_score,
            "MatchingSkills": list(matching_skills)
        }

        # Save the final result to S3.
        result_file_name = f"results/{job_id}_match_results.json"
        if not RESULTS_BUCKET:
            raise ValueError("RESULTS_BUCKET environment variable not set!")

        s3_client.put_object(
            Bucket=RESULTS_BUCKET,
            Key=result_file_name,
            Body=json.dumps(result_data)
        )
        print(f"Results saved to S3: {result_file_name}")

        return {'statusCode': 200, 'body': json.dumps(f"Resume processing complete. Match Score: {match_score}%")}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps(f"Error processing event: {str(e)}")}
