
import os
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from coldguard_agents import run_agent_workflow

st.set_page_config(page_title="ColdGuard AI", page_icon="🌡️", layout="wide")

st.title("🌡️ ColdGuard AI")
st.caption("Multi-Agent Pharmaceutical Cold-Chain Assessment — Step 4 Agent Workflow")

st.warning(
    "Student PoC only. Synthetic data and illustrative rules are not "
    "regulatory guidance. Never use this prototype for real medicine handling decisions."
)

ROOT = os.path.dirname(__file__)
SAMPLE_PATH = os.path.join(ROOT, "sample_temperature_logs.csv")
RULES_PATH = os.path.join(ROOT, "product_rules.csv")

rules_df = pd.read_csv(RULES_PATH)

st.header("1. Shipment data")

uploaded_file = st.file_uploader(
    "Upload a temperature log CSV",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        st.session_state["active_data"] = pd.read_csv(uploaded_file)
        st.session_state["active_data_source"] = "Uploaded CSV"
    except Exception as exc:
        st.error(f"Could not read this CSV: {exc}")
        st.stop()
else:
    if st.button("Load synthetic sample data"):
        st.session_state["active_data"] = pd.read_csv(SAMPLE_PATH)
        st.session_state["active_data_source"] = "Synthetic sample data"

data = st.session_state.get("active_data")

product = st.selectbox(
    "Select product",
    rules_df["product"].tolist()
)

if data is not None:
    st.subheader("Preview of temperature log")
    st.dataframe(data, use_container_width=True)

    st.caption(
        f"Source: {st.session_state.get('active_data_source', 'CSV data')}"
    )

    if st.button("Run multi-agent workflow", type="primary"):
        st.session_state["agent_run"] = run_agent_workflow(
            data, product, rules_df
        )
        st.session_state["agent_product"] = product

if (
    "agent_run" in st.session_state
    and st.session_state.get("agent_product") == product
):
    run = st.session_state["agent_run"]

    st.divider()
    st.header("2. Agent workflow trace")

    stages = [
        ("1. Planner Agent", "Creates the task plan"),
        ("2. Executor Agent", "Validates and analyzes the CSV"),
        ("3. Decision Agent", "Applies configured product rules"),
        ("4. Critic Agent", "Checks consistency and uncertainty"),
        ("5. Report Agent", "Builds the final structured report"),
    ]

    for title, desc in stages:
        st.write(f"**{title}** — {desc}")

    # AGENT 1: PLANNER
    with st.expander("View Planner Agent plan"):
        st.write(run["plan"]["plan"])

    # AGENT 2: EXECUTOR
    with st.expander("View Executor Agent checks"):
        st.write(
            "Tool functions called:",
            run["executor"]["tool_calls"]
        )
        st.write(
            "Validation messages:",
            run["executor"]["validation_errors"]
            or ["No input validation messages."]
        )

    # AGENT 3: DECISION — NEW DROPDOWN
    with st.expander("View Decision Agent output"):
        decision_output = run["decision"]

        st.write("**Status:**", decision_output["status"])
        st.write(decision_output["message"])

        decision_results = decision_output["results"]

        if not decision_results.empty:
            decision_table = decision_results[
                [
                    "shipment_id",
                    "preliminary_decision",
                    "preliminary_reason",
                ]
            ].rename(
                columns={
                    "shipment_id": "Shipment",
                    "preliminary_decision": "Preliminary decision",
                    "preliminary_reason": "Reason",
                }
            )

            st.dataframe(
                decision_table,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(
                "The Decision Agent could not generate decisions "
                "because the input could not be analyzed."
            )

    # AGENT 4: CRITIC
    with st.expander("View Critic Agent findings"):
        st.write(
            "**Consistency check passed:**",
            run["critic"]["passed"]
        )

        st.write(
            run["critic"]["issues"]
            or ["No issues detected by these basic checks."]
        )

    # FINAL REVIEWED RESULTS
    st.header("3. Final reviewed results")

    results = run["critic"]["results"]

    if not results.empty:
        display_results = results.drop(
            columns=["preliminary_decision", "preliminary_reason"],
            errors="ignore"
        )

        st.dataframe(
            display_results,
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Shipments analyzed", len(results))

        c2.metric(
            "Human review",
            int((results["decision"] == "Escalate to Human").sum())
        )

        c3.metric(
            "Critic findings",
            len(run["critic"]["issues"])
        )

        clean = run["executor"]["cleaned_data"]

        if not clean.empty:
            chosen = st.selectbox(
                "Choose shipment for temperature chart",
                clean["shipment_id"].unique().tolist()
            )

            chart = clean[clean["shipment_id"] == chosen]

            rule = rules_df[
                rules_df["product"] == product
            ].iloc[0]

            fig = px.line(
                chart,
                x="timestamp",
                y="temperature",
                markers=True,
                title=f"{chosen} temperature readings",
                labels={
                    "timestamp": "Time",
                    "temperature": "Temperature (°C)"
                }
            )

            fig.add_hline(
                y=float(rule["safe_min_c"]),
                line_dash="dash",
                annotation_text="Safe minimum"
            )

            fig.add_hline(
                y=float(rule["safe_max_c"]),
                line_dash="dash",
                annotation_text="Safe maximum"
            )

            st.plotly_chart(fig, use_container_width=True)

        # AGENT 5: REPORT
        report = run["report"]

        with st.expander("View Report Agent output"):
            st.json(report)

        report_csv = display_results.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download reviewed results CSV",
            report_csv,
            "coldguard_reviewed_results.csv",
            "text/csv"
        )

        report_json = json.dumps(
            report,
            indent=2,
            default=str
        ).encode("utf-8")

        st.download_button(
            "Download report JSON",
            report_json,
            "coldguard_report.json",
            "application/json"
        )

    else:
        st.error(
            "The workflow did not produce shipment results. "
            "Review validation messages."
        )

st.divider()
st.header("4. Illustrative product rules")

st.dataframe(
    rules_df,
    use_container_width=True,
    hide_index=True
)
