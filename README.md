# ColdGuard AI: Multi-Agent Pharmaceutical Cold-Chain Assessment

A domain-specific Agentic AI proof of concept developed for the CA-3 assessment. ColdGuard AI analyzes synthetic pharmaceutical shipment temperature logs using a collaborative, multi-agent workflow.

> **Disclaimer:** This is an academic proof of concept using synthetic data and illustrative rules. It is not intended for real pharmaceutical release, quarantine, or discard decisions.

## Problem Statement

Pharmaceutical products may require controlled temperatures during storage and transportation. Reviewing temperature logs manually is time-consuming and makes it harder to identify unusual readings, sensor gaps, and data-quality issues.

ColdGuard AI demonstrates how an agentic workflow can help organize and review shipment temperature information.

## Agent Workflow

```
Input log -> Planner -> Executor -> Decision -> Critic -> Report
                                                  |
                                                  +-> Escalate to Human (when evidence is insufficient)
```

| # | Agent | Responsibility |
|---|-------|----------------|
| 1 | **Planner Agent** | Creates an explicit five-step analysis plan for the selected product and records the number of input rows |
| 2 | **Executor Agent** | Runs the deterministic analysis tools (`validate_log`, `analyze_shipment`, `analyze_all`) to validate the log and estimate excursions and sensor gaps |
| 3 | **Decision Agent** | Converts the calculated results into a decision and reason using the selected product's illustrative rules. Does not invent missing evidence, and blocks if no results exist |
| 4 | **Critic Agent** | Checks decision consistency and data quality, records issues, and escalates uncertain shipments to a human |
| 5 | **Report Agent** | Builds a structured, evidence-based report from the recorded agent outputs |

### What the Critic Agent checks

- Only one valid reading, so duration cannot be estimated reliably
- Sensor gap longer than 30 minutes, so conditions during the gap are unknown
- A "Release" decision that conflicts with recorded out-of-range readings
- A "Discard" decision whose rationale should be verified against the product rules (flagged as a warning, never silently overridden)

Shipments with a single reading or a long sensor gap are changed to **Escalate to Human**, unless the decision is Discard, which is never silently overridden.

### What the report contains

Generation timestamp (UTC), product, analysis plan, input and valid row counts, validation errors, Critic result and issues, per-shipment decisions with reasons, and limitations.

## Technology Stack

- Python
- Streamlit
- Pandas
- Plotly
- Unittest

No paid APIs or external LLM services are required.

## Project Files

- `app.py`: Streamlit user interface
- `coldguard_agents.py`: Multi-agent workflow
- `coldguard_logic.py`: Temperature analysis and illustrative rules
- `coldguard_validation.py`: Input validation helpers
- `test_coldguard.py`: Automated tests
- `sample_temperature_logs.csv`: Synthetic shipment temperature readings
- `product_rules.csv`: Illustrative product thresholds
- `requirements.txt`: Python dependencies

## Setup and Execution

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Run the application**

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

**3. Run automated tests**

```bash
python -m unittest test_coldguard.py -v
```

## Validation and Testing

The project includes automated tests for:

- Missing columns
- Invalid temperatures
- Duplicate timestamps
- The sample dataset
- The agent workflow structure

Beyond the tests, the Executor validates every uploaded log, and the Critic independently flags data-quality and consistency issues in each run.

## Limitations

- Uses synthetic data and illustrative product rules.
- Estimates excursion durations by assuming each reading applies until the next reading.
- Cannot determine actual temperatures during unobserved intervals.
- Requires human review of ambiguous or unreliable records.
- Agents run in a fixed sequence; the Critic flags or escalates but does not re-run earlier agents.
- Has not been validated for real pharmaceutical operations.

## Future Scope

- Integrate real, authorized sensor data.
- Add audit logs and stronger data-quality monitoring.
- Improve evaluation using defined test cases and performance metrics.
- Explore secure integrations with inventory and shipment tracking systems.

## Academic Project

**Project:** ColdGuard AI
**Assessment:** CA-3, Domain-Specific Agentic AI Proof of Concept
