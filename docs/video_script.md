# Video Script Draft (Capstone Demo)

**Length**: ≤ 5 minutes

---

1. **Opening (30 s)**
   - Introduce yourself and the project title *RouteOpt Agent*.
   - Briefly state the problem: assigning drivers to loads while respecting a time limit.
   - Mention that a custom VRP optimizer lives in the backend and we expose it via a simple UI.

2. **Why Agents? (45 s)**
   - Explain the agent‑style workflow: distinct nodes for loading, validation, optimization, analysis, and explanation.
   - Show the architecture diagram (from `docs/architecture.md`).
   - Emphasise safety: local‑only execution, no secrets, deterministic results.

3. **Architecture Walk‑through (45 s)**
   - Point to the diagram and walk through each node.
   - Highlight that both the CLI (`app.py`) and the Streamlit app call the same `run_routing_workflow` function.

4. **Live Demo – Streamlit UI (2 min)
   - Launch the app: `streamlit run streamlit_app.py`.
   - Select a sample scenario (e.g., `sample_8_loads.txt`).
   - Adjust the driver time‑limit slider (show default 12.0).
   - Click **Run Optimization**.
   - Show the metrics tiles (initial/final drivers, time saved, feasibility).
   - Read the generated explanation text.
   - Scroll to the routes table and briefly explain the format.
   - Show the simple Matplotlib bar chart of stops per driver.
   - Mention that the UI works offline and no external services are called.

5. **Backend Validation (30 s)**
   - Switch to a terminal and run the original CLI command:
     ```bash
     python app.py data/sample_8_loads.txt --time-limit 12
     ```
   - Show that the textual output matches the UI explanation.
   - Run the test suite: `pytest -q` and note that all tests pass.

6. **Closing (30 s)**
   - Summarise the value: a deterministic, safety‑first vehicle‑routing tool wrapped in an easy‑to‑use UI.
   - Briefly outline future work (benchmarking, LLM‑driven explanations, richer visualisations).
   - Thank the audience and invite questions.

---

*All commands are run locally; no login or API keys are required.*
