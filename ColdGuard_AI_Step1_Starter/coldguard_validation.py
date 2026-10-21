"""Step 5 validation and test helpers for ColdGuard AI.

Rules are illustrative student PoC values, not pharmaceutical or regulatory guidance.
"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLUMNS = {"shipment_id", "timestamp", "temperature"}

def validate_and_prepare(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Validate schema and values; report issues instead of silently trusting bad rows."""
    messages = []
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        return pd.DataFrame(), [
            f"Missing required column(s): {', '.join(sorted(missing))}"
        ]

    df = data.copy()
    df["shipment_id"] = df["shipment_id"].astype("string").str.strip()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

    blank_ids = df["shipment_id"].isna() | (df["shipment_id"] == "")
    bad_timestamps = df["timestamp"].isna()
    bad_temps = df["temperature"].isna()
    if blank_ids.any():
        messages.append(f"{int(blank_ids.sum())} row(s) have a blank shipment_id.")
    if bad_timestamps.any():
        messages.append(f"{int(bad_timestamps.sum())} row(s) have invalid timestamps.")
    if bad_temps.any():
        messages.append(f"{int(bad_temps.sum())} row(s) have invalid temperatures.")

    valid = df.loc[~(blank_ids | bad_timestamps | bad_temps)].copy()
    duplicate_mask = valid.duplicated(["shipment_id", "timestamp"], keep=False)
    if duplicate_mask.any():
        messages.append(
            f"{int(duplicate_mask.sum())} row(s) share duplicate shipment/timestamp keys; "
            "duplicates are retained and require review."
        )

    # Detect impossible chronological ordering only after sorting; original order can be arbitrary.
    valid = valid.sort_values(["shipment_id", "timestamp"]).reset_index(drop=True)
    if valid.empty:
        messages.append("No valid rows remain after validation.")
    return valid, messages

def validate_workflow_output(workflow: dict) -> list[str]:
    """Check core structure and consistency across agent outputs."""
    issues = []
    for key in ["plan", "executor", "decision", "critic", "report"]:
        if key not in workflow:
            issues.append(f"Missing workflow stage: {key}")
    if issues:
        return issues

    executor_results = workflow["executor"]["results"]
    decision_results = workflow["decision"]["results"]
    critic_results = workflow["critic"]["results"]

    if not executor_results.empty and len(decision_results) != len(executor_results):
        issues.append("Decision Agent output count differs from Executor Agent output count.")
    if not decision_results.empty and len(critic_results) != len(decision_results):
        issues.append("Critic Agent output count differs from Decision Agent output count.")

    if not critic_results.empty:
        required = {"shipment_id", "decision", "decision_reason"}
        missing = required - set(critic_results.columns)
        if missing:
            issues.append(f"Final results missing columns: {', '.join(sorted(missing))}")

    return issues
