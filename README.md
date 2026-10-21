# ColdGuard AI — Multi-Agent Pharmaceutical Cold-Chain Assessment

## Overview
ColdGuard AI is a domain-specific Agentic AI proof of concept developed for the CA-3 assessment. It analyzes synthetic pharmaceutical shipment temperature logs using a collaborative, multi-agent workflow.

**Disclaimer:** This is an academic proof of concept using synthetic data and illustrative rules. It is not intended for real pharmaceutical release, quarantine, or discard decisions.

## Problem Statement
Pharmaceutical products may require controlled temperatures during storage and transportation. Reviewing temperature logs manually can be time-consuming and may make it harder to identify unusual readings, sensor gaps, and data-quality issues.

ColdGuard AI demonstrates how an agentic workflow can help organize and review shipment temperature information.

## Agent Workflow
1. **Planner Agent:** Creates the analysis plan.
2. **Executor Agent:** Validates and analyzes the temperature log.
3. **Decision Agent:** Applies the selected product's illustrative rules.
4. **Critic Agent:** Checks consistency and uncertainty.
5. **Report Agent:** Generates a structured report.

## Technology Stack
- Python
- Streamlit
- Pandas
- Plotly
- Unittest

## Project Files
- `app.py` — Streamlit user interface
- `coldguard_agents.py` — Multi-agent workflow
- `coldguard_logic.py` — Temperature analysis and illustrative rules
- `coldguard_validation.py` — Input validation helpers
- `test_coldguard.py` — Automated tests
- `sample_temperature_logs.csv` — Synthetic shipment temperature readings
- `product_rules.csv` — Illustrative product thresholds
- `requirements.txt` — Python dependencies

## Setup and Execution

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
streamlit run app.py
```

### 3. Run automated tests
```bash
python -m unittest test_coldguard.py -v
```

## Validation and Testing
The project includes automated tests for missing columns, invalid temperatures, duplicate timestamps, the sample dataset, and the agent workflow structure.

## Limitations
- Uses synthetic data and illustrative product rules.
- Estimates excursion durations between recorded readings.
- Cannot determine actual temperatures during unobserved intervals.
- Requires human review of ambiguous or unreliable records.
- Has not been validated for real pharmaceutical operations.

## Future Scope
- Integrate real, authorized sensor data.
- Add audit logs and stronger data-quality monitoring.
- Improve evaluation using defined test cases and performance metrics.
- Explore secure integrations with inventory and shipment tracking systems.

## Academic Project
**Project:** ColdGuard AI  
**Assessment:** CA-3 — Domain-Specific Agentic AI Proof of Concept

