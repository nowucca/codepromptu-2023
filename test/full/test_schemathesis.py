import pytest
import schemathesis

from . import BASE_URL, get_auth_basic_credentials, hooks
from .hooks import add_pytest_tag  # noqa

# Load the schema from the API.
# Replace "http://your-api-url/openapi.json" with the actual URL to your OpenAPI schema.
schema = schemathesis.from_uri(f"{BASE_URL}/openapi.json", base_url=f"{BASE_URL}", )


@schema.parametrize()
def test_private_endpoints(case):
    # Filter out tests that don't start with "/private"
    if not case.endpoint.path.startswith("/private"):
        pytest.skip("Skipping non-private endpoints")

    # For simplicity, adding basic auth to every test case.
    case.headers = {"Authorization": f"Basic {get_auth_basic_credentials()}"}
    print(case)

    response = case.call(timeout=4)
    case.validate_response(response)
