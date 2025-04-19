import React, { useState } from "react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";
import { Label } from "../ui/label";
import AWS from "aws-sdk"; // Import AWS SDK

// Configure AWS SDK with Cognito Identity Pool
AWS.config.update({
  region: "us-east-2", // Replace with your region
  credentials: new AWS.CognitoIdentityCredentials({
    IdentityPoolId: "us-east-2:605bc7ae-e4d0-4f0f-bef3-41d0a1855fcd", // Replace with your actual Cognito Identity Pool ID
  }),
});

const s3 = new AWS.S3(); // Create S3 instance

export default function ResumeMatchApp() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!resumeFile || !jobDescription.trim()) {
      alert("Please upload a resume and paste the job description");
      return;
    }

    setUploading(true);

    try {
      // Step 1: Upload the resume file to S3 using AWS SDK
      const params = {
        Bucket: "job-resume-upload-bucket", // Replace with your actual S3 bucket name
        Key: `${resumeFile.name}`, // File path in your S3 bucket
        Body: resumeFile, // The file content
        ContentType: resumeFile.type, // The file type
        // Optional: make the file publicly accessible
      };

      const s3Result = await s3.upload(params).promise(); // Upload the file to S3
      console.log("File uploaded to S3:", s3Result);

      // Step 2: Send SNS message with resume metadata and job description through API Gateway
      await sendToAPI(s3Result.Key, jobDescription); // Send the file key and job description to API
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Error uploading. Check console.");
    } finally {
      setUploading(false);
    }
  };

  // Step 3: Send SNS message via API Gateway (Lambda)
  const sendToAPI = async (fileKey, jobDescription) => {
    const message = { fileKey, jobDescription };

    try {
      // Assuming you have the ID token from Cognito stored in a variable called 'idToken'
      // const idToken = localStorage.getItem("idToken"); // Or however you store it

      const response = await fetch(
        "https://kfd6wew7dd.execute-api.us-east-2.amazonaws.com/harshProduction/upload",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(message),
        }
      );
      if (!response.ok) {
        throw new Error("Failed to send data to the server");
      }
      const data = await response.json();
      setResult(data);
      console.log("API response:", data);
    } catch (err) {
      console.error("Error sending to API:", err);
    }
  };
  return (
    <div className="container py-5">
      {/* Navbar */}
      <nav className="navbar navbar-expand-lg navbar-dark rounded shadow mb-4 heading1">
        <div className="container-fluid heading1">
          <a className="navbar-brand" href="#">
            Resume Matcher
          </a>
        </div>
      </nav>

      <Card className="p-5 shadow rounded bg-light">
        <CardContent className="space-y-4">
          <h2
            className="text-center mb-4 text-primary fw-bold"
            style={{ color: "#2b3bf0" }}
          >
            Upload your resume and paste the job description
          </h2>

          <Label className="form-label">Upload Resume (PDF)</Label>
          {/* Custom File Upload Button */}
          <br></br>
          <label htmlFor="file-upload" className="custom-file-upload">
            Choose File
          </label>
          <input
            id="file-upload"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            style={{
              display: "none", // Hide the default file input
            }}
          />
          <br></br>

          <Label className="form-label mt-3" for="jobDescription">
            Job Description
          </Label>
          <Textarea
            id="jobDescription"
            className="form-control mb-3"
            placeholder="Paste the job description here..."
            rows={6}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            style={{
              borderRadius: "10px",
              padding: "10px",
              border: "1px solid #ccc",
            }}
          />
          <Button
            className="btn btn-success w-100 mt-4"
            onClick={handleUpload}
            disabled={uploading}
            style={{
              borderRadius: "50px",
              padding: "12px 30px",
              fontSize: "18px",
              backgroundColor: "#28a745", // Always green
              borderColor: "#28a745",
            }}
          >
            {uploading ? "Processing..." : "Submit"}
          </Button>

          {result && (
            <div className="alert alert-info mt-4 animate__animated animate__fadeIn">
              <p>
                <strong>Match Score:</strong> {result.MatchScore}%
              </p>
              <p>
                <strong>Matching Skills:</strong>{" "}
                {result.MatchingSkills?.join(", ")}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Footer */}
      <footer className="text-center mt-5 text-muted">
        &copy; 2025 Resume Matcher | Powered by AWS & Textract
      </footer>
    </div>
  );
}
