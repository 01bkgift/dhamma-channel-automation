"""
Tests for AgentMonitoringStep.
"""
import json
import os
import shutil
import sys
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
    with patch("shutil.disk_usage") as mock_disk:
        mock_disk.return_value = (100, 50, 2 * 1024**3)
        
        with patch.dict(os.environ, {"TEST_SECRET": "value"}):
             # Mock config check to find .env file
             with patch("pathlib.Path.exists", return_value=True):
                 
                result = monitoring_step.execute(context)
                
                assert result["status"] == "success"
                assert result["checks"]["config"] is True
                assert result["checks"]["resources"] is True
                assert not result["issues"]
                
                # Verify JSON report content
                report_path = Path(result['report_file'])
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)

                assert report_data['status'] == 'success'
                assert not report_data['issues']
                assert report_data['checks']['resources'] is True

                # Verify Markdown summary content
                summary_path = Path(result['output_file'])
                summary_content = summary_path.read_text(encoding='utf-8')
                assert '✅ **System Healthy**' in summary_content
                assert 'No issues found' in summary_content


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


def test_warning_psutil_missing(monitoring_step, context):
    """Test warning when psutil is not installed."""
    context['check_memory'] = True
    with patch('shutil.disk_usage') as mock_disk, \
         patch.dict(os.environ, {'TEST_SECRET': 'value'}), \
         patch('pathlib.Path.exists', return_value=True):
        
        mock_disk.return_value = (100, 50, 2 * 1024**3)
        
        # Mock ImportError for psutil by manipulating sys.modules
        with patch.dict(sys.modules, {'psutil': None}):
            result = monitoring_step.execute(context)
            
            assert result['status'] == 'warning'
            assert any('RESOURCE_CHECK_SKIPPED: psutil_not_installed' in issue for issue in result['issues'])
            # Per rules, skipped check isn't failure, so resources is True if disk passed
            assert result['checks']['resources'] is True


def test_error_invalid_context(monitoring_step):
    """Test error status on invalid context."""
    # Context missing output_dir
    result = monitoring_step.execute({})
    assert result["status"] == "error"
    assert "Missing output_dir" in result["error"]
