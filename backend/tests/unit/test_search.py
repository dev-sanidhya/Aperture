from app.integrations.discovery.search import root_domain
from app.services.normalization import is_directory_domain, is_social_domain


def test_root_domain() -> None:
    assert root_domain("https://www.justdial.com/mumbai/foo") == "justdial.com"


def test_directory_and_social_domain_detection() -> None:
    assert is_directory_domain("https://www.justdial.com/mumbai/foo")
    assert is_social_domain("https://instagram.com/example")

