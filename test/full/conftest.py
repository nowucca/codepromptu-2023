import pytest
import requests

from . import BASE_URL, TEST_USERNAME, TEST_PASSWORD


@pytest.fixture(autouse=True)
def teardown_database():
    yield  # This marks the separation between setup and teardown. Since we only need teardown, nothing is before yield.

    # After test completion, perform the teardown:
    # Assuming you have a function/API to fetch prompts by tags
    response = requests.get(f"{BASE_URL}/private/prompt/tags?tags=pytest", auth=(f"{TEST_USERNAME}", f"{TEST_PASSWORD}"))
    if response.status_code == 200:
        for prompt in response.json():
            guid = prompt["guid"]
            # Delete the prompt with "pytest" tag
            requests.delete(f"{BASE_URL}/private/prompt/{guid}", auth=(f"{TEST_USERNAME}", f"{TEST_PASSWORD}"))
