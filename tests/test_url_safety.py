from src.url_safety import validate_public_https_url


def test_public_https_url_accepts_normal_authority_host():
    assert validate_public_https_url("https://data.example.gov.in/feed.geojson") == "https://data.example.gov.in/feed.geojson"


def test_public_https_url_rejects_http_and_embedded_credentials():
    for value in [
        "http://example.gov.in/feed.csv",
        "https://user:secret@example.gov.in/feed.csv",
    ]:
        try:
            validate_public_https_url(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe URL should be rejected: {value}")


def test_public_https_url_rejects_local_and_private_targets():
    for value in [
        "https://localhost/data",
        "https://service.local/data",
        "https://127.0.0.1/data",
        "https://10.0.0.5/data",
        "https://169.254.169.254/latest/meta-data",
        "https://[::1]/data",
    ]:
        try:
            validate_public_https_url(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"local/private URL should be rejected: {value}")
