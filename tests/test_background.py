import pytest
from unittest.mock import patch, MagicMock

from backend.startup import get_startup_command, install_startup, remove_startup, get_startup_status

def test_get_startup_command():
    cmd = get_startup_command()
    assert "backend.main --background" in cmd
    assert "w.exe" in cmd.lower() or "python" in cmd.lower()

@patch('winreg.OpenKey')
@patch('winreg.SetValueEx')
def test_install_startup(mock_setvalue, mock_openkey):
    install_startup()
    mock_openkey.assert_called_once()
    mock_setvalue.assert_called_once()

@patch('winreg.OpenKey')
@patch('winreg.DeleteValue')
def test_remove_startup(mock_delete, mock_openkey):
    remove_startup()
    mock_openkey.assert_called_once()
    mock_delete.assert_called_once()

@patch('winreg.OpenKey')
@patch('winreg.QueryValueEx')
def test_startup_status(mock_query, mock_openkey):
    mock_query.return_value = ("mock_path", 1)
    status = get_startup_status()
    assert status is True
