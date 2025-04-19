const express = require("express");
const cors = require("cors");
const fetch = require("node-fetch"); // Used to make requests to the AWS API

const app = express();
app.use(
  cors({
    origin: "https://dev.d2472r7hmvfd3i.amplifyapp.com",
    methods: ["GET", "POST", "OPTIONS", "PUT"], // Replace with your React frontend URL
  })
);
// Route to handle the request to AWS API
app.get("/data", (req, res) => {
  // Making a request to the AWS API
  fetch("https://a3kl6acoab.execute-api.us-east-2.amazonaws.com/prod")
    .then((response) => response.json()) // Parse the response as JSON
    .then((data) => {
      res.json(data); // Send the response from AWS API back to the frontend
    })
    .catch((error) => {
      res.status(500).json({ error: "Failed to fetch data from AWS API" });
    });
});

// Start the Express server on port 3000
app.listen(3000, () => console.log("Server is running on port 3000"));
