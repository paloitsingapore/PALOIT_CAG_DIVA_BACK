Prompt: Describe all the 3 endpoints created, for a PR

Answer:
For this PR, we have implemented three crucial endpoints for our Assisted Wayfinding system using AWS services. These endpoints handle face recognition, face indexing, and face enrollment. Here's a description of each:

1. Face Recognition Endpoint:
   - Path: `/recognize`
   - Method: POST
   - Description: This endpoint receives a base64-encoded image of a face and attempts to recognize it using Amazon Rekognition.
   - Workflow:
     a. Decodes the base64 image
     b. Temporarily uploads the image to S3
     c. Uses Rekognition to search for matching faces
     d. If a match is found, retrieves associated passenger data from DynamoDB
     e. Returns passenger data or a "no match found" message


2. Face Indexing Endpoint:
   - Path: `/index`
   - Method: POST
   - Description: This endpoint is used to index a new face in the Rekognition collection and store associated passenger data.
   - Request Body: Includes base64-encoded image and passenger data (name, passengerId, etc.)
   - Workflow:
     a. Decodes the base64 image
     b. Uploads the image to S3
     c. Indexes the face using Amazon Rekognition
     d. Stores passenger data in DynamoDB
   - Implementation details can be found in the `adding_rekognition.md` file:
   

**Response:**
- Success (200 OK):
  ```json
  {
    "faceId": "string",
    "message": "Face indexed successfully"
  }
  ```
- Error (500 Internal Server Error):
  ```json
  {
    "error": "Error message"
  }
  ```

**Implementation Details:**
The indexing process involves the following steps:
1. Decode the base64 image.
2. Upload the image to an S3 bucket.
3. Index the face using Amazon Rekognition.
4. Store passenger data in DynamoDB.



5. Face Enrollment Endpoint:
   - Path: `/enroll`
   - Method: POST
   - Description: This endpoint handles the process of enrolling a new face into the system, which involves both indexing the face and storing associated passenger information.
   - Request Body: Similar to the indexing endpoint, includes base64-encoded image and passenger data
   - Workflow:
     a. Validates input data
     b. Decodes the base64 image
     c. Uploads the image to S3
     d. Indexes the face using Amazon Rekognition
     e. Stores passenger data in DynamoDB
     f. Returns a success message with the generated faceId

These endpoints are implemented as Lambda functions and are exposed through API Gateway. The necessary AWS resources (Lambda functions, IAM roles, API Gateway) are set up using AWS CDK, as shown in the `AssistedWayfindingBackendStack` class.

Prompt: Add also an explanation for the GUI:

Answer:
In addition to the backend endpoints we've implemented, we've also developed a GUI testing


1. Face Recognition Component:
   - This component uses the device's camera to capture the passenger's face.
   - It sends the captured image to the `/recognize` endpoint for face recognition.
   - If a match is found, it displays the passenger's information and wayfinding instructions.
   - If no match is found, it prompts the user to enroll or try again.

2. Face Enrollment Component:
   - This component is used when a new passenger needs to be enrolled in the system.
   - It captures the passenger's face image and collects necessary information (name, passenger ID, etc.).
   - The collected data is sent to the `/enroll` endpoint to register the passenger in the system.

3. Wayfinding Display:
   - Once a passenger is recognized, this component shows personalized wayfinding information.
   - It may include directions to the gate, estimated walking time, and any special accommodations (e.g., wheelchair assistance).

4. Error Handling and User Feedback:
   - The GUI provides clear feedback to users throughout the process.
   - It handles errors gracefully, showing user-friendly messages for various scenarios (e.g., network issues, recognition failures).

