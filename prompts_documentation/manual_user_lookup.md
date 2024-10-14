s# Manual User Lookup API

## Overview

The Manual User Lookup API provides a fallback mechanism for retrieving passenger information when face recognition fails or is unavailable. This API allows airport staff to manually look up a passenger's data using their name, date of birth, and flight number.

## API Endpoint

```
GET /manual-lookup
```

## Request Parameters

The API accepts the following query parameters:

| Parameter    | Type   | Required | Description                           |
|--------------|--------|----------|---------------------------------------|
| name         | string | Yes      | The passenger's full name             |
| dateOfBirth  | string | Yes      | The passenger's date of birth (YYYY-MM-DD) |
| flightNumber | string | Yes      | The passenger's flight number         |

## Response Format

The API returns a JSON object with the following structure:

### Successful Response (200 OK)

```json
{
  "userData": {
    "userId": "string",
    "name": "string",
    "dateOfBirth": "string",
    "passengerId": "string",
    "changi_app_user_id": "string",
    "next_flight_id": "string",
    "has_lounge_access": boolean,
    "accessibilityPreferences": {
      "increaseFontSize": boolean,
      "wheelchairAccessibility": boolean
    },
    "language": "string"
  }
}
```

### Error Responses

- **400 Bad Request**: Missing required fields
- **404 Not Found**: User not found
- **500 Internal Server Error**: Server-side error

Error responses will have the following structure:

```json
{
  "error": "string"
}
```

## Example Usage

### Request

```
GET /manual-lookup?name=John%20Doe&dateOfBirth=1990-01-01&flightNumber=SQ123
```

### Successful Response

```json
{
  "userData": {
    "userId": "user_john_doe",
    "name": "John Doe",
    "dateOfBirth": "1990-01-01",
    "passengerId": "passenger_john_doe",
    "changi_app_user_id": "CAU12345SQ",
    "next_flight_id": "SQ123",
    "has_lounge_access": true,
    "accessibilityPreferences": {
      "increaseFontSize": false,
      "wheelchairAccessibility": true
    },
    "language": "en"
  }
}
```

### Error Response (User Not Found)

```json
{
  "error": "User not found"
}
```

## Security Considerations

1. This API should only be accessible to authorized airport staff.
2. Implement rate limiting to prevent abuse.
3. Use HTTPS to encrypt all API traffic.
4. Consider implementing additional authentication mechanisms (e.g., API keys, OAuth2) for enhanced security.

## Integration with Face Recognition System

The Manual User Lookup API is designed to work alongside the face recognition system:

1. When face recognition fails to identify a passenger, the system should prompt the staff to use this manual lookup feature.
2. The staff can then input the passenger's name, date of birth, and flight number to retrieve their information.
3. Once the passenger is identified, their data can be used to provide personalized assistance or update the face recognition system if necessary.

## Error Handling

The API implements robust error handling to provide clear feedback:

- If any required fields are missing, it returns a 400 Bad Request error.
- If no user is found matching the provided details, it returns a 404 Not Found error.
- For any server-side issues, it returns a 500 Internal Server Error.

Always check the response status code and handle errors appropriately in your client application.

## Performance Considerations

- The API uses a scan operation on DynamoDB, which can be inefficient for large tables. 
- If performance becomes an issue, consider implementing a Global Secondary Index (GSI) on the combination of name, dateOfBirth, and next_flight_id for more efficient querying.

## Conclusion

The Manual User Lookup API provides a crucial fallback mechanism for the Assisted Wayfinding system. By allowing manual lookups, it ensures that passengers can still receive personalized assistance even when face recognition is not available or fails. Proper integration of this API with the existing system will significantly enhance the overall reliability and user experience of the Assisted Wayfinding solution.