import os

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.environ.get(
    "API_ENDPOINT_URL"
)  # Ensure this is set in your environment or CI/CD pipeline


# Skip for now, as we don't have a map image bucket
# @pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL not set")
# def test_successful_direction_retrieval():
#     response = requests.get(f"{API_BASE_URL}/directions/kiosk_1/gate_b4")

#     assert response.status_code == 200
#     data = response.json()
#     assert data["from"] == "kiosk_1"
#     assert data["to"] == "gate_b4"
#     assert "map_image" in data
#     assert (
#         data["map_image"]
#         == "https://assistedwayfinding-map-images-dev.s3.amazonaws.com/maps/kiosk_1_to_gate_b4.png"
#     )
#     assert "direction_steps" in data
#     assert len(data["direction_steps"]) > 0


@pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL not set")
def test_map_image_not_found():
    response = requests.get(f"{API_BASE_URL}/directions/kiosk_1/nonexistent_gate")

    assert response.status_code == 200
    data = response.json()
    assert data["from"] == "kiosk_1"
    assert data["to"] == "nonexistent_gate"
    assert "map_image" in data
    assert data["map_image"] == ""
    assert "direction_steps" in data
    assert len(data["direction_steps"]) > 0


@pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL not set")
def test_invalid_bucket_access():
    # This test assumes that the MAP_IMAGE_BUCKET is set incorrectly for this environment
    # You might need to set up a specific environment where the bucket access is forbidden
    response = requests.get(f"{API_BASE_URL}/directions/kiosk_1/gate_b4")

    assert response.status_code == 200
    data = response.json()
    # Even if access is forbidden, the Lambda should handle it gracefully and return an empty map_image
    assert data["map_image"] == ""


@pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL not set")
def test_missing_parameters():
    response = requests.get(f"{API_BASE_URL}/directions/")

    assert response.status_code == 403  # Expecting 403 if authentication is required

    data = response.json()
    assert "message" in data
    assert data["message"] == "Missing Authentication Token"


@pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL not set")
def test_random_directions() -> None:
    from_location = "lobby"
    to_location = "gate_c"
    response = requests.get(f"{API_BASE_URL}/directions/{from_location}/{to_location}")

    assert response.status_code == 200
    data = response.json()
    assert data["from"] == from_location
    assert data["to"] == to_location
    assert "map_image" in data  # Could be present or not
    assert "direction_steps" in data
    assert len(data["direction_steps"]) > 0
