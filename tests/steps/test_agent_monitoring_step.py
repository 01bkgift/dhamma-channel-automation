"""
Tests for AgentMonitoringStep.
"""
import json
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from steps.agent_monitoring import AgentMonitoringStep


@pytest.fixture
def monitoring_step():
    return AgentMonitoringStep()


@pytest.fixture
def context(tmp_path):
    return {
        "output_dir": str(tmp_path / "artifacts"),
        "check_disk_space": True,
        "min_disk_GB": 1,
        "check_memory": False,
        "required_secrets": ["TEST_SECRET"]
    }


def test_success_all_pass(monitoring_step, context, tmp_path):
    """Test successful execution with all checks passing."""
    with patch("shutil.disk_usage") as mock_disk, \
         patch("os.environ.get") as mock_env, \
         patch("pathlib.Path.exists") as mock_exists:
        
        # Mock disk space > 1GB (return total, used, free in bytes)
        # 2GB free
        mock_disk.return_value = (100, 50, 2 * 1024**3)
        
        # Mock secret presence
        mock_env.return_value = "secret_value"
        
        # Mock .env file existence (any call to exists for env files returns True)
        # We need to be careful not to break other exists calls.
        # But for unit test logic, we can just ensure 'prod.env' or '.env' check returns True.
        # Actually easier to use fs/tmp_path.
        
        # Create dummy .env
        (Path(context["output_dir"])).mkdir(parents=True, exist_ok=True)
        (Path("prod.env")).touch() # This interacts with real FS if not mocked.
        # Let's mock Path.exists specifically for env files logic
        def side_effect(self):
            if str(self).endswith(".env"):
                return True
            return False
            
    # Better approach: Don't mock Path.exists globally. Create real file.
    # Note: The test runs in a temp dir usually if configured? No, pytest doesn't change CWD by default.
    # We should use patches for isolation.
    
    with patch("shutil.disk_usage") as mock_disk:
        mock_disk.return_value = (100, 50, 2 * 1024**3)
        
        with patch.dict(os.environ, {"TEST_SECRET": "value"}):
             # Mock config check to find .env file
             with patch("pathlib.Path.exists", return_value=True):
                 
                result = monitoring_step.execute(context)
                
                assert result["status"] == "success"
                assert result["checks"]["system"] is True
                assert result["checks"]["config"] is True
                assert result["checks"]["resources"] is True
                assert not result["issues"]
                
                # Check output files
                assert Path(result["output_file"]).exists()
                assert Path(result["report_file"]).exists()


def test_warning_low_disk(monitoring_step, context):
    """Test warning when disk space is low."""
    with patch("shutil.disk_usage") as mock_disk:
        # 0.5 GB free (below 1GB limit)
        mock_disk.return_value = (100, 50, 0.5 * 1024**3)
        
        with patch.dict(os.environ, {"TEST_SECRET": "value"}):
            with patch("pathlib.Path.exists", return_value=True):
                result = monitoring_step.execute(context)
                
                assert result["status"] == "warning"
                assert result["checks"]["resources"] is False
                assert any("LOW_DISK_SPACE" in issue for issue in result["issues"])


def test_warning_missing_secret(monitoring_step, context):
    """Test warning when required secret is missing."""
    with patch("shutil.disk_usage") as mock_disk:
        mock_disk.return_value = (100, 50, 2 * 1024**3)
        
        # Ensure secret is NOT in environment
        with patch.dict(os.environ, {}, clear=True):
             with patch("pathlib.Path.exists", return_value=True):
                result = monitoring_step.execute(context)
                
                assert result["status"] == "warning"
                assert result["checks"]["config"] is False
                assert "MISSING_SECRET: TEST_SECRET" in result["issues"]


def test_warning_missing_env_file(monitoring_step, context):
    """Test warning when no .env file exists."""
    with patch("shutil.disk_usage") as mock_disk:
        mock_disk.return_value = (100, 50, 2 * 1024**3)
        
        with patch.dict(os.environ, {"TEST_SECRET": "value"}):
            # Mock Path.exists to return False for env checks
            # The code checks Path("prod.env").exists() and Path(".env").exists()
            with patch("pathlib.Path.exists", return_value=False):
                result = monitoring_step.execute(context)
                
                assert result["status"] == "warning"
                assert result["checks"]["config"] is False
                assert "MISSING_ENV_FILE: neither prod.env nor .env found" in result["issues"]


def test_error_invalid_context(monitoring_step):
    """Test error status on invalid context."""
    # Context missing output_dir
    result = monitoring_step.execute({})
    assert result["status"] == "error"
    assert "Missing output_dir" in result["error"]
