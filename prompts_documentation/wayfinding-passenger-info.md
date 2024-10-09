

Certainly! Documenting an API is crucial for ensuring that developers understand how to interact with it effectively. Below is a detailed documentation for the Directions API, which includes endpoint details, request parameters, response structure, and examples.

---

# Directions API Documentation

The Directions API provides endpoints to retrieve navigation directions between specified locations within a facility. It also optionally provides a map image URL if available.

## Base URL

The base URL for the API is:

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

Replace `{api-id}`, `{region}`, and `{stage}` with your specific API Gateway details.

## Endpoints

### 1. Get Directions

**Endpoint:**

```
GET /directions/{from}/{to}
```

**Description:**

Retrieves navigation directions from the specified `from` location to the `to` location. Optionally returns a map image URL if available in the S3 bucket.

**Path Parameters:**

- `from` (string): The starting location.
- `to` (string): The destination location.

**Query Parameters:**

None.

**Headers:**

- `x-api-key` (optional): Your API key if the API Gateway requires it.
- `Authorization` (optional): Bearer token or other authentication credentials if required.

**Response:**

- **Status Code: 200 OK**

  ```json
  {
    "from": "checkin",
    "to": "gate_b4",
    "map_image": "https://assistedwayfinding-map-images-dev.s3.amazonaws.com/maps/checkin_to_gate_b4.png",
    "direction_steps": [
      {"step": "Leave checkin and turn right", "duration": "1 min"},
      {"step": "Continue up escalator", "duration": "1 min"},
      {"step": "Turn right", "duration": "8 min"},
      {"step": "Turn left", "duration": "3 min"},
      {"step": "Arrive at gate B4", "duration": "0 min"}
    ]
  }
  ```

- **Status Code: 404 Not Found**

  ```json
  {
    "error": "Not Found",
    "message": "The specified path does not exist."
  }
  ```

- **Status Code: 400 Bad Request**

  ```json
  {
    "error": "Bad Request",
    "message": "Missing required parameter: {parameter_name}"
  }
  ```

- **Status Code: 403 Forbidden**

  ```json
  {
    "message": "Missing Authentication Token"
  }
  ```

**Error Handling:**

- **400 Bad Request**: Returned if required path parameters are missing.
- **403 Forbidden**: Returned if authentication is required but not provided.
- **404 Not Found**: Returned if the specified path does not exist.

**Examples:**

- **Request:**

  ```http
  GET /directions/checkin/gate_b4 HTTP/1.1
  Host: {api-id}.execute-api.{region}.amazonaws.com
  x-api-key: your-api-key
  ```

- **Response:**

  ```json
  {
    "from": "checkin",
    "to": "gate_b4",
    "map_image": "https://assistedwayfinding-map-images-dev.s3.amazonaws.com/maps/checkin_to_gate_b4.png",
    "direction_steps": [
      {"step": "Leave checkin and turn right", "duration": "1 min"},
      {"step": "Continue up escalator", "duration": "1 min"},
      {"step": "Turn right", "duration": "8 min"},
      {"step": "Turn left", "duration": "3 min"},
      {"step": "Arrive at gate B4", "duration": "0 min"}
    ]
  }
  ```

## Authentication

The API may require authentication depending on your API Gateway configuration. Ensure you provide the necessary credentials:

- **API Key**: Include in the `x-api-key` header if required.
- **Bearer Token**: Include in the `Authorization` header if using a custom authorizer.

## Rate Limiting

The API may be subject to rate limiting. Ensure you handle HTTP 429 responses gracefully and implement retry logic as needed.

## Notes

- Ensure that the `from` and `to` locations are valid and recognized by the system.
- The map image URL is only provided if the corresponding image exists in the S3 bucket.

---

This documentation provides a comprehensive overview of the Directions API, including how to make requests, handle responses, and manage errors. Adjust the details as necessary to fit your specific implementation and deployment environment.