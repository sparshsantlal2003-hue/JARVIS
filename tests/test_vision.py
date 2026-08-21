import pytest
from unittest.mock import patch, MagicMock

# We need to mock settings before importing the vision modules
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('backend.vision.analyzer.settings') as mock:
        mock.vision_enabled = True
        mock.vision_min_confidence = 0.80
        mock.vision_max_retries = 2
        yield mock

@pytest.fixture
def mock_vision_provider():
    with patch('backend.vision.analyzer.vision_provider') as mock:
        yield mock

@pytest.fixture
def mock_capture():
    with patch('backend.vision.analyzer.capture') as mock:
        # Return a dummy image size
        mock.get_screen_size.return_value = (1920, 1080)
        yield mock

@pytest.fixture
def mock_window_detector():
    with patch('backend.vision.analyzer.window_detector') as mock:
        mock.get_active_window.return_value = {
            "title": "Test Window",
            "left": 0, "top": 0, "right": 1920, "bottom": 1080,
            "width": 1920, "height": 1080
        }
        yield mock

def test_describe_screen(mock_capture, mock_window_detector, mock_vision_provider):
    from backend.vision.analyzer import analyzer
    
    mock_vision_provider.analyze_screen.return_value = "The screen shows a Test Window."
    
    result = analyzer.describe_screen()
    
    assert "Test Window" in result
    mock_capture.capture_screen.assert_called_once()
    mock_vision_provider.analyze_screen.assert_called_once()
    mock_capture.cleanup.assert_called_once()

def test_locate_element_success(mock_capture, mock_window_detector, mock_vision_provider):
    from backend.vision.analyzer import analyzer
    
    mock_vision_provider.locate_element.return_value = {"x": 100, "y": 200, "confidence": 0.95}
    
    result = analyzer.locate_element("Button")
    
    assert result is not None
    assert result["x"] == 100
    assert result["y"] == 200
    assert result["confidence"] == 0.95
    assert result["active_window"] == "Test Window"
    mock_capture.cleanup.assert_called_once()

def test_locate_element_low_confidence(mock_capture, mock_window_detector, mock_vision_provider):
    from backend.vision.analyzer import analyzer
    
    mock_vision_provider.locate_element.return_value = {"x": 100, "y": 200, "confidence": 0.50}
    
    result = analyzer.locate_element("Button")
    
    assert result is None  # Below 0.80 threshold

def test_verify_state(mock_capture, mock_window_detector, mock_vision_provider):
    from backend.vision.analyzer import analyzer
    
    mock_vision_provider.analyze_screen.return_value = "yes"
    
    assert analyzer.verify_state("Is the button visible?") == True
    
    mock_vision_provider.analyze_screen.return_value = "no"
    assert analyzer.verify_state("Is the window closed?") == False
