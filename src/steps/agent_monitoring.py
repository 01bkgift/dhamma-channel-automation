"""
Agent Monitoring Step.
Performs pre-flight health checks on resources and configuration.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, TypedDict

from automation_core.base_step import BaseStep

logger = logging.getLogger(__name__)


class MonitoringContext(TypedDict, total=False):
    """Context for AgentMonitoringStep."""
    output_dir: str
    check_disk_space: bool
    min_disk_GB: int | float
    check_memory: bool
    required_secrets: list[str]


class AgentMonitoringStep(BaseStep):
    """
    One-shot guardian step to validate environment readiness.
    Checks disk, memory, and configuration secrets.
    """

    def __init__(self) -> None:
        super().__init__(
            step_id="agent_monitoring",
            step_type="AgentMonitoring",
            version="1.0.0"
        )

    def execute(self, context: MonitoringContext) -> dict:
        """
        Execute the monitoring checks.
        
        Returns:
            dict: The result dictionary adhering to the contract.
        """
        # Parse context with defaults
        output_dir_str = context.get("output_dir")
        if not output_dir_str:
            return {
                "status": "error",
                "error": "Missing output_dir in context"
            }
            
        output_dir = Path(output_dir_str)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Unable to create output_dir: {e}"
            }

        check_disk = context.get("check_disk_space", True)
        min_disk_gb = context.get("min_disk_GB", 2)
        check_mem = context.get("check_memory", True)
        req_secrets = context.get("required_secrets", ["YOUTUBE_API_KEY"])

        issues: list[str] = []
        checks = {
            "config": True,
            "resources": True
        }

        # 1. Resource Checks
        # Disk
        if check_disk:
            try:
                total, used, free = shutil.disk_usage(".")
                free_gb = free / (1024**3)
                if free_gb < min_disk_gb:
                    checks["resources"] = False
                    issues.append(f"LOW_DISK_SPACE: available={free_gb:.2f}GB required={min_disk_gb}GB")
            except Exception as e:
                checks["resources"] = False
                issues.append(f"DISK_CHECK_FAILED: {e}")

        # Memory (Optional dependency psutil)
        if check_mem:
            try:
                import psutil  # type: ignore
                mem = psutil.virtual_memory()
                # Heuristic: Warn if available memory is very low.
                # This threshold is configurable via the 'min_memory_MB' context parameter.
                min_memory_mb = context.get("min_memory_MB", 500)
                available_mb = mem.available / (1024**2)
                if available_mb < min_memory_mb:
                     checks["resources"] = False
                     issues.append(f"LOW_MEMORY: available={available_mb:.2f}MB required={min_memory_mb}MB")

            except ImportError:
                # Mark check as passed (as per prompt rules) but warn
                issues.append("RESOURCE_CHECK_SKIPPED: psutil_not_installed")
            except Exception as e:
                checks["resources"] = False
                issues.append(f"MEMORY_CHECK_FAILED: {e}")

        # 2. Configuration Checks
        # Env File
        env_files = ["prod.env", ".env"]
        env_found = any(Path(f).exists() for f in env_files)
        if not env_found:
            checks["config"] = False
            issues.append("MISSING_ENV_FILE: neither prod.env nor .env found")

        # Secrets
        # We need to check actual environment variables, assuming they are loaded.
        # However, BaseStep/Orchestrator usually loads env.
        # We check os.environ.
        if req_secrets:
            for secret in req_secrets:
                val = os.environ.get(secret)
                if not val or not val.strip():
                    checks["config"] = False
                    issues.append(f"MISSING_SECRET: {secret}")
                else:
                    logger.info("Secret %s is present", secret)

        # Determine Status
        status = "success"
        if issues:
            status = "warning"
            # If strictly checking fails, we report warning. 
            # Prompt says: "Return 'status': 'warning' if any of the following occur"
            # And "Warnings must NOT crash the pipeline"
            
        # Write Artifacts
        output_file = output_dir / "monitoring_summary.md"
        report_file = output_dir / "monitoring_report.json"
        
        self._write_report(report_file, checks, issues, status)
        self._write_summary(output_file, checks, issues)

        return {
            "status": status,
            "output_file": str(output_file),
            "report_file": str(report_file),
            "checks": checks,
            "issues": issues
        }

    def _write_report(self, path: Path, checks: dict, issues: list[str], status: str) -> None:
        data = {
            "status": status,
            "checks": checks,
            "issues": issues
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)

    def _write_summary(self, path: Path, checks: dict, issues: list[str]) -> None:
        lines = ["# 🛡️ Agent Monitoring Summary", ""]
        
        lines.append("## Status")
        if issues:
            lines.append("⚠️ **WARNING: Issues Detected**")
        else:
            lines.append("✅ **System Healthy**")
        lines.append("")

        lines.append("## Checks")
        lines.append(f"- System Resources: {'✅' if checks['resources'] else '⚠️'}")
        lines.append(f"- Configuration: {'✅' if checks['config'] else '⚠️'}")
        lines.append("")

        if issues:
            lines.append("## Issues")
            for issue in issues:
                lines.append(f"- ❌ `{issue}`")
        else:
            lines.append("No issues found. Ready for takeoff 🚀")
            
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
