
"""ColdGuard AI analysis engine — illustrative student PoC only.

These rules are synthetic and must not be used for real pharmaceutical
release, quarantine, or discard decisions.
"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"shipment_id", "timestamp", "temperature"}


def validate_log(data: pd.DataFrame):
    """Validate input, report data-quality problems, and prepare valid rows."""
    errors = []

    if data is None or data.empty:
        return pd.DataFrame(), ["The uploaded dataset is empty."]

    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        return pd.DataFrame(), [
            f"Missing required column(s): {', '.join(sorted(missing))}"
        ]

    cleaned = data.copy()

    cleaned["shipment_id"] = (
        cleaned["shipment_id"].astype("string").str.strip()
    )
    cleaned["timestamp"] = pd.to_datetime(
        cleaned["timestamp"], errors="coerce"
    )
    cleaned["temperature"] = pd.to_numeric(
        cleaned["temperature"], errors="coerce"
    )

    blank_ids = cleaned["shipment_id"].isna() | (
        cleaned["shipment_id"] == ""
    )
    bad_timestamps = cleaned["timestamp"].isna()
    bad_temperatures = cleaned["temperature"].isna()

    invalid_rows = blank_ids | bad_timestamps | bad_temperatures

    if blank_ids.any():
        errors.append(
            f"{int(blank_ids.sum())} row(s) have a blank shipment_id."
        )

    if bad_timestamps.any():
        errors.append(
            f"{int(bad_timestamps.sum())} row(s) have invalid or blank timestamps."
        )

    if bad_temperatures.any():
        errors.append(
            f"{int(bad_temperatures.sum())} row(s) have invalid or blank temperatures."
        )

    removed_count = int(invalid_rows.sum())
    cleaned = cleaned.loc[~invalid_rows].copy()

    if removed_count:
        errors.append(
            f"{removed_count} invalid row(s) excluded from analysis."
        )

    # Detect duplicate shipment/timestamp pairs before analysis.
    duplicate_mask = cleaned.duplicated(
        subset=["shipment_id", "timestamp"], keep=False
    )

    duplicate_shipments = set(
        cleaned.loc[duplicate_mask, "shipment_id"].dropna().astype(str)
    )

    if duplicate_mask.any():
        errors.append(
            f"{int(duplicate_mask.sum())} row(s) have duplicate "
            "shipment/timestamp keys. Affected shipments require human review."
        )

    cleaned = cleaned.sort_values(
        ["shipment_id", "timestamp"]
    ).reset_index(drop=True)

    if cleaned.empty:
        errors.append("No valid rows remain after input validation.")

    return cleaned, errors


def analyze_shipment(group: pd.DataFrame, rule: dict) -> dict:
    """Calculate illustrative temperature metrics for one shipment."""
    group = group.sort_values("timestamp").reset_index(drop=True)

    temps = group["temperature"]
    times = group["timestamp"]

    safe_min = float(rule["safe_min_c"])
    safe_max = float(rule["safe_max_c"])
    max_gap = float(rule["sensor_gap_escalation_min"])

    total_out = 0.0
    high_duration = 0.0
    gap_durations = []

    below_discard = bool(
        (temps < float(rule["discard_if_below_c"])).any()
    )
    high_threshold = float(rule["discard_if_above_c"])
    max_temp = float(temps.max())
    min_temp = float(temps.min())

    out_count = int(
        ((temps < safe_min) | (temps > safe_max)).sum()
    )

    for i in range(len(group) - 1):
        temp = float(temps.iloc[i])
        delta = max(
            0.0,
            (times.iloc[i + 1] - times.iloc[i]).total_seconds() / 60.0,
        )

        if delta > max_gap:
            gap_durations.append(delta)

        # Approximation only: assumes a reading represents the interval
        # until the next reading. Actual temperatures are unknown between readings.
        if temp < safe_min or temp > safe_max:
            total_out += delta

        if temp > high_threshold:
            high_duration += delta

    largest_gap = max(gap_durations, default=0.0)

    discard_high = (
        max_temp > high_threshold
        and high_duration
        > float(rule["discard_if_above_duration_min"])
    )

    limit = float(rule["max_cumulative_out_of_range_min"])
    pct = float(rule["borderline_percent"]) / 100.0

    borderline = (
        limit > 0
        and limit * (1 - pct) <= total_out <= limit * (1 + pct)
    )

    if below_discard or discard_high:
        decision = "Discard"
        reason = "An illustrative discard condition was triggered."

    elif largest_gap > max_gap:
        decision = "Escalate to Human"
        reason = (
            f"Sensor gap ({largest_gap:.0f} min) exceeds "
            f"{max_gap:.0f} min; the unobserved interval is unknown."
        )

    elif borderline:
        decision = "Escalate to Human"
        reason = (
            "Estimated excursion duration is close to "
            "the illustrative limit."
        )

    elif out_count == 0:
        decision = "Release"
        reason = (
            "All recorded temperatures are within the illustrative "
            "safe range and no long sensor gap was detected."
        )

    elif total_out <= limit:
        decision = "Release with note"
        reason = (
            f"Estimated out-of-range duration ({total_out:.0f} min) "
            f"is within the illustrative limit ({limit:.0f} min)."
        )

    else:
        decision = "Quarantine"
        reason = (
            f"Estimated out-of-range duration ({total_out:.0f} min) "
            f"exceeds the illustrative limit ({limit:.0f} min)."
        )

    return {
        "shipment_id": str(group["shipment_id"].iloc[0]),
        "readings": len(group),
        "min_temperature_c": round(min_temp, 2),
        "max_temperature_c": round(max_temp, 2),
        "out_of_range_readings": out_count,
        "estimated_out_of_range_min": round(total_out, 2),
        "estimated_high_threshold_duration_min": round(
            high_duration, 2
        ),
        "largest_sensor_gap_min": round(largest_gap, 2),
        "preliminary_decision": decision,
        "preliminary_reason": reason,
    }


def analyze_all(data: pd.DataFrame, product: str, rules_df: pd.DataFrame):
    """Validate data and analyze shipments using the selected illustrative rule."""
    cleaned, errors = validate_log(data)

    if cleaned.empty:
        return pd.DataFrame(), errors, cleaned

    if "product" not in rules_df.columns:
        return (
            pd.DataFrame(),
            errors + ["Product rules are missing the 'product' column."],
            cleaned,
        )

    selected = rules_df[rules_df["product"] == product]

    if selected.empty:
        return (
            pd.DataFrame(),
            errors + [f"No rule found for product: {product}"],
            cleaned,
        )

    required_rule_columns = {
        "safe_min_c",
        "safe_max_c",
        "sensor_gap_escalation_min",
        "discard_if_below_c",
        "discard_if_above_c",
        "discard_if_above_duration_min",
        "max_cumulative_out_of_range_min",
        "borderline_percent",
    }

    missing_rules = required_rule_columns - set(selected.columns)

    if missing_rules:
        return (
            pd.DataFrame(),
            errors + [
                "Product rules are missing required column(s): "
                + ", ".join(sorted(missing_rules))
            ],
            cleaned,
        )

    rule = selected.iloc[0].to_dict()

    results = [
        analyze_shipment(group, rule)
        for _, group in cleaned.groupby("shipment_id", sort=True)
    ]

    results_df = pd.DataFrame(results)

    # A duplicate timestamp makes interval-based estimates ambiguous.
    # Do not automatically treat the affected shipment as safe.
    duplicate_mask = cleaned.duplicated(
        subset=["shipment_id", "timestamp"], keep=False
    )
    duplicate_shipments = set(
        cleaned.loc[duplicate_mask, "shipment_id"].dropna().astype(str)
    )

    if duplicate_shipments:
        affected = results_df["shipment_id"].astype(str).isin(
            duplicate_shipments
        )
        results_df.loc[affected, "preliminary_decision"] = (
            "Escalate to Human"
        )
        results_df.loc[affected, "preliminary_reason"] = (
            "Duplicate timestamps make the temperature timeline ambiguous; "
            "manual review is required."
        )

    return results_df, errors, cleaned
