import streamlit as st
import subprocess
import time
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
CAD_INPUT_DIR = "cad_inputs"
LIVE_FILE = "current_measurement.txt"
RESULT_FILE = "component_comparison_report.csv"
SNAPSHOT_FILE = "inspection_snapshot.jpg"   # optional future use

ABS_TOL_MM = 2.0        # same tolerance used in backend
TREND_POINTS = 10       # last N inspections

os.makedirs(CAD_INPUT_DIR, exist_ok=True)

st.set_page_config(
    page_title="Automated Dimensional Inspection",
    layout="wide"
)

# =====================================================
# UI HEADER
# =====================================================
st.title("Automated Dimensional Inspection System")
st.caption("CAD-based real-time quality inspection")

# =====================================================
# SIDEBAR – INPUTS
# =====================================================
st.sidebar.header("Inspection Setup")

component = st.sidebar.selectbox(
    "Select Component Type",
    ["", "Ball Bearing", "Washer", "Square Washer", "Hex Nut"]
)

uploaded_file = st.sidebar.file_uploader(
    "Upload CAD File (DXF)",
    type=["dxf"]
)

start_btn = st.sidebar.button("Start Inspection", type="primary")

# =====================================================
# VALIDATION
# =====================================================
if start_btn:
    if not component:
        st.sidebar.error("Please select a component type.")
        st.stop()

    if uploaded_file is None:
        st.sidebar.error("Please upload a DXF file.")
        st.stop()

# =====================================================
# SAVE DXF FILE
# =====================================================
if start_btn:
    dxf_path = os.path.join(CAD_INPUT_DIR, uploaded_file.name)
    with open(dxf_path, "wb") as f:
        f.write(uploaded_file.read())

    st.sidebar.success(f"DXF saved: {uploaded_file.name}")

# =====================================================
# START BACKEND PIPELINE
# =====================================================
if start_btn:
    st.info("Starting CAD extraction and inspection pipeline...")

    process = subprocess.Popen(
        ["python", "main.py", dxf_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # =================================================
    # LIVE OUTPUT SECTION
    # =================================================
    st.subheader("Live Measurement Output")
    live_box = st.empty()

    while process.poll() is None:
        if os.path.exists(LIVE_FILE):
            with open(LIVE_FILE, "r") as f:
                live_box.code(f.read())
        time.sleep(0.5)

    st.success("Inspection completed.")

# =====================================================
# FINAL RESULT VISUALIZATION
# =====================================================
if os.path.exists(RESULT_FILE):
    df = pd.read_csv(RESULT_FILE)
    last = df.iloc[-1]

    st.markdown("## Final Inspection Result")

    # ---------------- OVERALL STATUS CARD ----------------
    if last["status"] == "DEFECTIVE":
        st.markdown(
            """
            <div style="background:#ffdddd;padding:20px;border-radius:12px;">
                <h1 style="color:#b30000;text-align:center;">❌ COMPONENT DEFECTIVE</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.error("🔔 Defect detected!")
        st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3", autoplay=True)
    else:
        st.markdown(
            """
            <div style="background:#ddffdd;padding:20px;border-radius:12px;">
                <h1 style="color:#006600;text-align:center;">✅ COMPONENT NOT DEFECTIVE</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ---------------- INSPECTION DASHBOARD ----------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Inspections", len(df))

    with col2:
        st.metric("Defective Count", (df["status"] == "DEFECTIVE").sum())

    with col3:
        st.metric("Pass Rate (%)",
                  round(100 * (df["status"] == "NOT DEFECTIVE").mean(), 1))

    st.markdown("---")

    # ---------------- DIMENSION COMPARISON ----------------
    st.subheader("Dimension-wise Comparison")

    for col in df.columns:
        if col.startswith("MEAS_"):
            dim = col.replace("MEAS_", "")
            cad_col = f"CAD_{dim}"
            err_col = f"{dim}_abs_err"

            if cad_col not in df.columns or err_col not in df.columns:
                continue

            cad = last[cad_col]
            meas = last[col]
            err = last[err_col]

            c1, c2, c3, c4 = st.columns([2, 2, 2, 4])

            with c1:
                st.metric("CAD (mm)", f"{cad:.2f}")

            with c2:
                st.metric("Measured (mm)", f"{meas:.2f}")

            with c3:
                st.metric("Error (mm)", f"{err:.2f}")

            # -------- Gauge Meter --------
            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=err,
                number={'suffix': " mm"},
                gauge={
                    'axis': {'range': [0, ABS_TOL_MM * 1.5]},
                    'bar': {'color': "red" if err > ABS_TOL_MM else "green"},
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': ABS_TOL_MM
                    }
                }
            ))
            gauge.update_layout(height=220, margin=dict(t=10, b=10))
            c4.plotly_chart(gauge, use_container_width=True)

            if err <= ABS_TOL_MM:
                st.success("Within tolerance")
            else:
                st.error("Out of tolerance")

            st.markdown("---")

    # ---------------- ERROR TREND ----------------
    st.subheader("Error Trend (Last Inspections)")

    trend_df = df.tail(TREND_POINTS)
    err_cols = [c for c in trend_df.columns if c.endswith("_abs_err")]

    for err_col in err_cols:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(trend_df))),
            y=trend_df[err_col],
            mode="lines+markers",
            name=err_col
        ))
        fig.add_hline(y=ABS_TOL_MM, line_dash="dash", line_color="red")
        fig.update_layout(
            title=f"Trend: {err_col}",
            xaxis_title="Inspection Index",
            yaxis_title="Error (mm)",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- SNAPSHOT PLACEHOLDER ----------------
    st.subheader("Inspection Snapshot")

    if os.path.exists(SNAPSHOT_FILE):
        st.image(SNAPSHOT_FILE, caption="Captured Inspection Frame")
    else:
        st.info("Camera snapshot will appear here (optional future feature).")

else:
    st.info("No inspection results available yet.")

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption("Powered by CAD + Computer Vision Inspection Pipeline")
