import pytest
from unittest.mock import patch, MagicMock
from backend.tools.registry import ToolRegistry
from backend.tools.windows_apps import launch_application

def test_registry_registration():
    registry = ToolRegistry()
    
    @registry.register
    def dummy_tool(x: int):
        return x * 2
        
    assert len(registry.get_all_tools()) == 1
    assert registry.execute("dummy_tool", {"x": 5}) == 10
    
def test_registry_unknown_tool():
    registry = ToolRegistry()
    result = registry.execute("unknown", {})
    assert result["success"] is False
    assert "not found" in result["error"]

@patch("backend.tools.windows_apps.subprocess.Popen")
def test_launch_application_success(mock_popen):
    result = launch_application("notepad")
    assert result["success"] is True
    assert result["application"] == "Notepad"
    mock_popen.assert_called_once()
    
    # Test alias
    mock_popen.reset_mock()
    result = launch_application("calc")
    assert result["success"] is True
    assert result["application"] == "Calculator"
    mock_popen.assert_called_once()

def test_launch_application_unsupported():
    result = launch_application("arbitrary_hacker_tool")
    assert result["success"] is False
    assert "not in the allowed application registry" in result["error"]

import os
import pathlib
from unittest.mock import patch, mock_open
from backend.tools.keyboard import type_text, press_key
from backend.tools.mouse import move_mouse, click_mouse
from backend.tools.files import _is_safe_path, list_directory, create_directory, read_text_file, write_text_file

# --- KEYBOARD TESTS ---
@patch("backend.tools.keyboard.pyautogui.write")
def test_type_text(mock_write):
    res = type_text("hello")
    assert res["success"] is True
    mock_write.assert_called_once_with("hello", interval=0.01)

@patch("backend.tools.keyboard.pyautogui.press")
def test_press_key_valid(mock_press):
    res = press_key("enter")
    assert res["success"] is True
    mock_press.assert_called_once_with("enter")

def test_press_key_invalid():
    res = press_key("unsupported_key")
    assert res["success"] is False
    assert "not in the allowed safe key list" in res["error"]

# --- MOUSE TESTS ---
@patch("backend.tools.mouse.pyautogui.moveTo")
def test_move_mouse_valid(mock_move):
    res = move_mouse(100, 100)
    assert res["success"] is True
    mock_move.assert_called_once_with(100, 100, duration=0.25)

def test_move_mouse_invalid():
    res = move_mouse(-10, 50000)
    assert res["success"] is False

# --- FILESYSTEM TESTS ---
def test_path_validation_safe():
    safe_path = str(pathlib.Path(os.path.expanduser("~")) / "Desktop" / "test.txt")
    assert _is_safe_path(safe_path) is True

def test_path_validation_unsafe():
    unsafe_path = "C:\\Windows\\System32\\cmd.exe"
    assert _is_safe_path(unsafe_path) is False
    
def test_path_validation_traversal():
    # Attempt traversal from a safe directory
    base = str(pathlib.Path(os.path.expanduser("~")))
    traversal_path = os.path.join(base, "..", "..", "Windows")
    assert _is_safe_path(traversal_path) is False

@patch("backend.tools.files._is_safe_path", return_value=True)
@patch("os.makedirs")
def test_create_directory(mock_makedirs, mock_is_safe):
    res = create_directory("dummy_path")
    assert res["success"] is True
    mock_makedirs.assert_called_once_with("dummy_path", exist_ok=True)

@patch("backend.tools.files._is_safe_path", return_value=False)
def test_create_directory_unsafe(mock_is_safe):
    res = create_directory("dummy_path")
    assert res["success"] is False
    assert "Access denied" in res["error"]

@patch("backend.tools.files._is_safe_path", return_value=True)
def test_read_file(mock_is_safe):
    with patch("builtins.open", mock_open(read_data="test data")):
        res = read_text_file("dummy.txt")
        assert res["success"] is True
        assert res["content"] == "test data"

@patch("backend.tools.files._is_safe_path", return_value=True)
def test_write_file(mock_is_safe):
    m = mock_open()
    with patch("builtins.open", m):
        res = write_text_file("dummy.txt", "new data")
        assert res["success"] is True
    m().write.assert_called_once_with("new data")
