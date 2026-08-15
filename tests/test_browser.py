import pytest
from backend.tools.browser.navigation import is_safe_url, ensure_protocol

def test_url_validation():
    assert is_safe_url("https://example.com")
    assert is_safe_url("http://google.com")
    assert is_safe_url("example.com") # Implicitly safe, prepended later
    assert not is_safe_url("file:///etc/passwd")
    assert not is_safe_url("javascript:alert(1)")
    assert not is_safe_url("data:text/html,<html>")

def test_ensure_protocol():
    assert ensure_protocol("example.com") == "https://example.com"
    assert ensure_protocol("http://example.com") == "http://example.com"
    assert ensure_protocol("https://example.com") == "https://example.com"
