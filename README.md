# AI-Powered Network Sentinel

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![ESP8266](https://img.shields.io/badge/Hardware-NodeMCU%20ESP8266-0EA5E9)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Model](https://img.shields.io/badge/Model-Isolation%20Forest-22C55E)
![Status](https://img.shields.io/badge/Status-Real--Time%20Detection-16A34A)

Real-time wireless anomaly detection using NodeMCU (ESP8266) + Python + Streamlit.

This project captures live Wi-Fi packet telemetry from a NodeMCU running in promiscuous mode, streams packet features over serial, and applies an unsupervised Isolation Forest model to detect suspicious behavior in near real time.

## Demo

### Video Demo

GitHub README pages do not reliably render embedded `<video>` tags.

[Watch the demo video (MP4)](d8c2ad97-4a4a-4e81-ab5c-8aaf683f47b1.mp4)

### CLI Demo Results

![CLI Demo Result 1](cli%20sam.jpeg)![CLI Demo Result 2](cli%20sample.jpeg)

## Project Overview

AI-Powered Network Sentinel is a hardware-software security prototype built from scratch across three layers:

- Hardware layer: ESP8266 (NodeMCU) sniffing nearby Wi-Fi traffic and sending packet metadata over USB serial.
- AI layer: Python-based anomaly detection using IsolationForest with rolling-window learning.
- Frontend layer: Dark-mode Streamlit dashboard for live status cards, telemetry charting, and anomaly logs.

The model is unsupervised, so it does not require labeled attack data. It learns what current traffic patterns look like and flags outliers as potential attacks.

## Key Features

- Real-time packet ingest from NodeMCU over serial (COM3 at 115200 baud).
- Unsupervised anomaly detection (Isolation Forest).
- Live SOC-style dashboard in Streamlit (dark cybersecurity theme).
- Three live metrics:
  - System status (SECURE / ATTACK DETECTED)
  - Latest packet type
  - Current RSSI
- Live RSSI line chart with anomaly highlighting and threshold line.
- Sidebar AI Confidence control (contamination tuning).
- Last 10 anomaly events with timestamps.
- Console monitoring mode for lightweight terminal operation.

## Repository Structure

- brain.py: Console runtime for serial + AI detection output.
- streamlit_app.py: Real-time Streamlit dashboard.
- sentinel_core.py: Shared serial parsing and detection logic used by both modes.
- sniffer.ino: NodeMCU firmware for packet sniffing + serial telemetry output.
- brain.md: Conceptual explanation of the original Python detection workflow.

## How It Works

1) NodeMCU capture
- sniffer.ino configures ESP8266 in station + promiscuous mode.
- Callback extracts packet type and RSSI from received frames.
- Data is sent as comma-separated serial lines:

  type,rssi

2) Python ingestion and modeling
- Python reads serial lines continuously.
- Parsed packets are stored in a rolling buffer.
- After warmup, IsolationForest is trained on the latest window.
- The newest packet is scored:
  - 1 = normal
  - -1 = anomaly

3) Output layer
- Console mode prints secure/anomaly status per packet.
- Streamlit mode updates cards, chart, and anomaly logs using st.empty() in a while loop.

## Hardware Requirements

- NodeMCU ESP8266 board
- USB cable
- Laptop/PC (Windows tested)

## Software Requirements

- Python 3.10+ recommended
- Arduino IDE (for flashing sniffer.ino)
- Python packages:
  - pyserial
  - pandas
  - scikit-learn
  - streamlit
  - plotly

## Installation

1) Clone repository and enter directory.

2) Install Python dependencies:

    pip install pyserial pandas scikit-learn streamlit plotly

3) Flash firmware:
- Open sniffer.ino in Arduino IDE.
- Select your NodeMCU board and COM port.
- Upload sketch.

4) Verify serial port:
- Ensure Python scripts use the same port as your board.
- Default in this project is COM3.

## Usage

### A) Console Monitoring Mode

Run:

    python brain.py

Expected output examples:

    SYSTEM SECURE   | Pkt: 132 | RSSI: 181
    ANOMALY DETECTED | Pkt: 8 | RSSI: 180

### B) Streamlit Dashboard Mode

Run:

    python -m streamlit run streamlit_app.py

Open the local URL shown in terminal (usually http://localhost:8501).

Dashboard includes:
- Header: AI-Powered Network Sentinel
- Subtitle: Unsupervised Anomaly Detection via NodeMCU
- Live 3-column metrics
- Live RSSI chart with anomaly markers and threshold line
- Sidebar AI Confidence slider
- Logs table (last 10 anomalies)

## Model and Tuning Notes

- Algorithm: IsolationForest
- Default contamination is controlled in dashboard by AI Confidence slider.
- Lower contamination values generally make detector more sensitive to rare deviations.
- Warmup packets are used so the model has enough baseline context before scoring.

## Data Format

Serial telemetry expected from NodeMCU:

    packet_type,rssi

Example:

    132,-68

If parsing fails or malformed lines arrive, they are skipped.

## Troubleshooting

### 1) Streamlit command fails
Use:

    python -m streamlit run streamlit_app.py

Do not use:

    python run streamlit_app.py

### 2) module 'serial' has no attribute 'Serial'
Cause: wrong package named serial installed instead of pyserial in active interpreter.
Fix:

    python -m pip uninstall -y serial
    python -m pip install pyserial

### 3) Cannot open COM port
- Confirm board is connected.
- Close Serial Monitor/other apps using same COM port.
- Update COM port in code if board enumerates as a different port.

### 4) No chart updates
- Confirm NodeMCU is actually sending lines.
- Validate baud rate matches (115200).
- Verify Plotly is installed.

## Security and Ethical Notice

This project is intended for defensive research, education, and authorized monitoring only. Do not use packet sniffing or network monitoring on networks you do not own or have explicit permission to test.

## Future Improvements

- Persistent storage for logs and model snapshots.
- Multi-feature packet extraction (channel, subtype, rates).
- Adaptive thresholding and drift handling.
- Alert integrations (email, webhook, SIEM).
- Multi-sensor fusion (Wi-Fi + BLE + RF).

## Credits

Built as an end-to-end security prototype combining:
- Embedded firmware (ESP8266)
- Real-time machine learning (Isolation Forest)
- Live cybersecurity visualization (Streamlit)
