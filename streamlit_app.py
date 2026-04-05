from datetime import datetime
import time

import pandas as pd
import streamlit as st
from sentinel_core import MAX_BUFFER, detect_packet, open_serial, parse_packet_line
MAX_LOG_ROWS = 10


def init_session_state() -> None:
    if "packet_history" not in st.session_state:
        st.session_state.packet_history = []
    if "anomaly_logs" not in st.session_state:
        st.session_state.anomaly_logs = []


def status_card(title: str, value: str, accent: str, subtitle: str) -> str:
    return f"""
    <div class="sentinel-card" style="border-color: {accent}; box-shadow: 0 0 0 1px rgba(255,255,255,0.04), 0 0 24px {accent}22;">
        <div class="card-label">{title}</div>
        <div class="card-value" style="color: {accent};">{value}</div>
        <div class="card-subtext">{subtitle}</div>
    </div>
    """


def build_chart(frame: pd.DataFrame, threshold: float | None = None):
    try:
        import plotly.graph_objects as go

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=frame["timestamp"],
                y=frame["rssi"],
                mode="lines",
                name="RSSI",
                line=dict(color="#38bdf8", width=2),
            )
        )

        anomalies = frame[frame["anomaly"] == True]
        if not anomalies.empty:
            figure.add_trace(
                go.Scatter(
                    x=anomalies["timestamp"],
                    y=anomalies["rssi"],
                    mode="markers",
                    name="Anomaly",
                    marker=dict(color="#ef4444", size=10, symbol="x"),
                )
            )

        if threshold is not None:
            figure.add_hline(
                y=threshold,
                line_color="#f87171",
                line_width=2,
                line_dash="dash",
                annotation_text="Alert Threshold",
                annotation_position="top left",
            )

        figure.update_layout(
            template="plotly_dark",
            height=520,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        figure.update_xaxes(showgrid=False)
        figure.update_yaxes(gridcolor="rgba(148, 163, 184, 0.15)")
        return figure
    except Exception:
        return None


def main() -> None:
    st.set_page_config(
        page_title="AI-Powered Network Sentinel",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(14, 165, 233, 0.14), transparent 24%),
                    radial-gradient(circle at top right, rgba(239, 68, 68, 0.10), transparent 20%),
                    linear-gradient(180deg, #020617 0%, #0f172a 52%, #020617 100%);
                color: #e2e8f0;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 1.5rem;
            }
            .hero-title {
                font-size: clamp(2.1rem, 4vw, 4.2rem);
                font-weight: 800;
                line-height: 1.02;
                letter-spacing: -0.04em;
                color: #f8fafc;
                margin-bottom: 0.35rem;
            }
            .hero-subtitle {
                font-size: 1.02rem;
                color: #94a3b8;
                margin-bottom: 1.2rem;
            }
            .status-strip {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.45rem 0.8rem;
                border: 1px solid rgba(148, 163, 184, 0.2);
                background: rgba(15, 23, 42, 0.55);
                border-radius: 999px;
                color: #cbd5e1;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }
            .sentinel-card {
                min-height: 150px;
                border: 1px solid rgba(148, 163, 184, 0.2);
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.85), rgba(2, 6, 23, 0.95));
                border-radius: 20px;
                padding: 1.2rem 1.1rem;
            }
            .card-label {
                color: #94a3b8;
                font-size: 0.82rem;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                margin-bottom: 0.85rem;
            }
            .card-value {
                font-size: 2.05rem;
                font-weight: 800;
                letter-spacing: -0.04em;
                margin-bottom: 0.35rem;
            }
            .card-subtext {
                color: #cbd5e1;
                font-size: 0.95rem;
            }
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(2, 6, 23, 0.98));
                border-right: 1px solid rgba(148, 163, 184, 0.16);
            }
            .sidebar-title {
                color: #f8fafc;
                font-size: 1.15rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }
            .sidebar-note {
                color: #94a3b8;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="status-strip">LIVE • NodeMCU Serial Stream • Unsupervised AI Monitoring</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">AI-Powered Network Sentinel</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Unsupervised Anomaly Detection via NodeMCU</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="sidebar-title">Control Center</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-note">Tune the detector sensitivity before starting the live stream. Lower values increase anomaly sensitivity.</div>', unsafe_allow_html=True)
    confidence_level = st.sidebar.slider("AI Confidence", min_value=1, max_value=10, value=3, help="Adjust contamination/sensitivity")
    contamination = confidence_level / 100.0
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Logs")
    st.sidebar.caption("The last 10 anomalies remain visible in the dashboard.")

    init_session_state()

    try:
        ser = open_serial()
    except Exception as exc:
        st.error(f"Connection Error: {exc}")
        st.stop()

    data_buffer: list[list[int]] = []

    status_placeholder = st.empty()
    metric_row = st.columns(3)
    packet_placeholder = metric_row[0].empty()
    rssi_placeholder = metric_row[1].empty()
    stream_placeholder = metric_row[2].empty()

    chart_placeholder = st.empty()
    logs_placeholder = st.empty()

    chart_placeholder.info("Waiting for packets from the serial feed...")
    logs_placeholder.info("No anomalies detected yet.")

    while True:
        try:
            raw_line = ser.readline().decode("utf-8", errors="ignore").strip()
            values = parse_packet_line(raw_line)
            if values is None:
                time.sleep(0.05)
                continue

            data_buffer.append(values)

            if len(data_buffer) > MAX_BUFFER:
                data_buffer.pop(0)

            result = detect_packet(data_buffer, values, contamination)
            packet_type = result.packet_type
            rssi = result.rssi
            anomaly_flag = result.anomaly
            confidence_text = result.score_label

            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.packet_history.append(
                {
                    "timestamp": timestamp,
                    "rssi": rssi,
                    "anomaly": anomaly_flag,
                }
            )
            if len(st.session_state.packet_history) > MAX_BUFFER:
                st.session_state.packet_history.pop(0)

            if anomaly_flag:
                st.session_state.anomaly_logs.append(
                    {
                        "Timestamp": timestamp,
                        "Packet Type": packet_type,
                        "RSSI": rssi,
                        "Status": "ATTACK DETECTED",
                    }
                )
                if len(st.session_state.anomaly_logs) > MAX_LOG_ROWS:
                    st.session_state.anomaly_logs = st.session_state.anomaly_logs[-MAX_LOG_ROWS:]

            status_color = "#22c55e" if not anomaly_flag else "#ef4444"
            status_value = "SECURE" if not anomaly_flag else "ATTACK DETECTED"
            status_subtitle = "Telemetry within expected bounds" if not anomaly_flag else "AI flagged a suspicious packet pattern"

            status_placeholder.markdown(
                status_card("System Status", status_value, status_color, status_subtitle),
                unsafe_allow_html=True,
            )
            packet_placeholder.markdown(
                status_card("Packet Type", str(packet_type), "#38bdf8", f"Latest packet received at {timestamp}"),
                unsafe_allow_html=True,
            )
            rssi_placeholder.markdown(
                status_card("Signal Strength (RSSI)", str(rssi), "#f59e0b", f"Current decibel level at {timestamp}"),
                unsafe_allow_html=True,
            )
            stream_placeholder.markdown(
                status_card("Stream State", confidence_text, "#a78bfa", f"AI confidence set to {confidence_level}% contamination"),
                unsafe_allow_html=True,
            )

            chart_frame = pd.DataFrame(st.session_state.packet_history)
            threshold = None
            if not chart_frame.empty:
                threshold = float(chart_frame["rssi"].quantile(0.2))
            chart = build_chart(chart_frame, threshold=threshold) if not chart_frame.empty else None
            if chart is not None:
                chart_placeholder.plotly_chart(chart, use_container_width=True)
            else:
                chart_placeholder.info("Waiting for enough data to render the live chart...")

            if st.session_state.anomaly_logs:
                logs_frame = pd.DataFrame(st.session_state.anomaly_logs[-MAX_LOG_ROWS:])
                logs_placeholder.dataframe(logs_frame, use_container_width=True, hide_index=True)
            else:
                logs_placeholder.info("No anomalies detected yet.")

            time.sleep(0.08)
        except KeyboardInterrupt:
            ser.close()
            st.warning("Live monitoring stopped.")
            break
        except Exception:
            continue


if __name__ == "__main__":
    main()