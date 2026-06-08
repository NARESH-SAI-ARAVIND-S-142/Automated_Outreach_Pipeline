"""
Shared HTTP client with automatic retry, exponential backoff,
and consistent timeout handling for all API calls.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
    timeout: tuple = (30, 60),
) -> requests.Session:
    """
    Create a requests.Session with automatic retry on transient errors.

    Args:
        max_retries: Maximum number of retries per request.
        backoff_factor: Exponential backoff multiplier (2 = 1s, 2s, 4s...).
        status_forcelist: HTTP status codes to retry on.
        timeout: Default (connect, read) timeout in seconds.

    Returns:
        Configured requests.Session.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Store default timeout on session for use in API modules
    session.timeout = timeout

    return session


def handle_response(response: requests.Response, service_name: str) -> dict:
    """
    Handle an API response — raise clear errors for common failure modes.

    Args:
        response: The requests Response object.
        service_name: Name of the service (for error messages).

    Returns:
        Parsed JSON response as dict.

    Raises:
        requests.HTTPError: With a descriptive message on failure.
    """
    if response.status_code == 401:
        raise requests.HTTPError(
            f"[{service_name}] Authentication failed (401). "
            f"Check your API key in .env.",
            response=response,
        )

    if response.status_code == 429:
        raise requests.HTTPError(
            f"[{service_name}] Rate limit exceeded (429). "
            f"The request was retried but still failed. "
            f"Wait a moment and try again.",
            response=response,
        )

    if response.status_code >= 400:
        # Try to extract a meaningful error message from the response body
        try:
            body = response.json()
            error_msg = body.get("error", body.get("message", str(body)))
        except Exception:
            error_msg = response.text[:200]

        raise requests.HTTPError(
            f"[{service_name}] API error {response.status_code}: {error_msg}",
            response=response,
        )

    try:
        return response.json()
    except ValueError:
        raise requests.HTTPError(
            f"[{service_name}] Invalid JSON response: {response.text[:200]}",
            response=response,
        )
