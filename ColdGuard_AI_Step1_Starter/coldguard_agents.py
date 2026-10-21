"""Five cooperating ColdGuard agents. Rule values are illustrative only."""
from __future__ import annotations
from datetime import datetime, timezone
import pandas as pd
from coldguard_logic import analyze_all

def planner_agent(data: pd.DataFrame, product: str) -> dict:
    """Creates an explicit task plan for this analysis."""
    return {
        "agent": "Planner Agent",
        "plan": [
            "Validate the uploaded columns and values",
            "Analyze readings, excursion estimates, and sensor gaps",
            "Apply the selected product's illustrative rules",
            "Critic Agent checks data quality and decision consistency",
            "Report Agent prepares the evidence-based report",
        ],
        "product": product,
        "input_rows": int(len(data)),
    }

def executor_agent(data: pd.DataFrame, product: str, rules_df: pd.DataFrame) -> dict:
    """Runs the deterministic analysis tools."""
    results, errors, cleaned = analyze_all(data, product, rules_df)
    return {
        "agent": "Executor Agent",
        "results": results,
        "validation_errors": errors,
        "cleaned_data": cleaned,
        "tool_calls": ["validate_log", "analyze_shipment", "analyze_all"],
    }

def decision_agent(executor_output: dict) -> dict:
    """Turns calculations into a decision object without inventing missing evidence."""
    results = executor_output["results"].copy()
    if results.empty:
        return {"agent": "Decision Agent", "results": results, "status": "blocked",
                "message": "No decisions generated because the input could not be analyzed."}
    results["decision"] = results["preliminary_decision"]
    results["decision_reason"] = results["preliminary_reason"]
    return {"agent": "Decision Agent", "results": results, "status": "completed",
            "message": "Preliminary decisions generated from configured illustrative rules."}

def critic_agent(executor_output: dict, decision_output: dict) -> dict:
    """Independently checks obvious consistency/data-quality issues and may escalate."""
    results = decision_output["results"].copy()
    issues = list(executor_output["validation_errors"])
    if results.empty:
        return {"agent": "Critic Agent", "passed": False, "issues": issues or ["No results to validate."],
                "results": results}
    for _, row in results.iterrows():
        sid = row["shipment_id"]
        if int(row["readings"]) < 2:
            issues.append(f"{sid}: only one valid reading; duration cannot be estimated reliably.")
        if float(row["largest_sensor_gap_min"]) > 30:
            issues.append(f"{sid}: long sensor gap means conditions during the gap are unknown.")
        if row["decision"] == "Release" and int(row["out_of_range_readings"]) > 0:
            issues.append(f"{sid}: Release conflicts with recorded out-of-range readings.")
        if row["decision"] == "Discard" and not (
            float(row["min_temperature_c"]) < 0
            or (float(row["max_temperature_c"]) > 0 and
                float(row["estimated_high_threshold_duration_min"]) > 0)
        ):
            # This is a conservative warning, not a replacement policy.
            issues.append(f"{sid}: verify discard rationale against configured product rules.")
    # Escalate any shipment with material data uncertainty; do not silently override discard.
    for idx, row in results.iterrows():
        sid = row["shipment_id"]
        if int(row["readings"]) < 2 or float(row["largest_sensor_gap_min"]) > 30:
            if row["decision"] != "Discard":
                results.at[idx, "decision"] = "Escalate to Human"
                results.at[idx, "decision_reason"] = "Critic Agent flagged insufficient or discontinuous evidence; human review required."
    return {"agent": "Critic Agent", "passed": len(issues) == 0, "issues": issues, "results": results}

def report_agent(plan: dict, executor_output: dict, critic_output: dict, product: str) -> dict:
    """Builds a report object from recorded outputs."""
    results = critic_output["results"]
    decisions = results[["shipment_id", "decision", "decision_reason"]].to_dict("records") if not results.empty else []
    return {
        "agent": "Report Agent",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "product": product,
        "plan": plan["plan"],
        "input_rows": plan["input_rows"],
        "valid_rows_analyzed": int(len(executor_output["cleaned_data"])),
        "validation_errors": executor_output["validation_errors"],
        "critic_passed": critic_output["passed"],
        "critic_issues": critic_output["issues"],
        "shipment_decisions": decisions,
        "limitations": [
            "Synthetic student demonstration; rules are illustrative and not regulatory guidance.",
            "Excursion duration is estimated by assuming each reading applies until the next reading.",
            "Temperatures during sensor gaps are unknown.",
            "Human review is required before any real-world decision.",
        ],
    }

def run_agent_workflow(data: pd.DataFrame, product: str, rules_df: pd.DataFrame) -> dict:
    """Orchestrates all agents in sequence and returns the complete trace."""
    plan = planner_agent(data, product)
    executor = executor_agent(data, product, rules_df)
    decision = decision_agent(executor)
    critic = critic_agent(executor, decision)
    report = report_agent(plan, executor, critic, product)
    return {"plan": plan, "executor": executor, "decision": decision,
            "critic": critic, "report": report}
