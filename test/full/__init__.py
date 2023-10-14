from dotenv import load_dotenv
import os
import base64

load_dotenv()

BASE_URL="http://aitools.cs.vt.edu:8000"
TEST_USERNAME = os.getenv('TEST_USERNAME')
TEST_PASSWORD = os.getenv('TEST_PASSWORD')


def get_auth_basic_credentials():
    # Ensure the variables are set
    if not TEST_USERNAME or not TEST_PASSWORD:
        raise ValueError("Both TEST_USERNAME and TEST_PASSWORD must be set!")

    # Encode the credentials
    credentials = f"{TEST_USERNAME}:{TEST_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    return encoded_credentials
