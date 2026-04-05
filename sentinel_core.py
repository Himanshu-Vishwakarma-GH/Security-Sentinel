from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import serial
from sklearn.ensemble import IsolationForest


SERIAL_PORT = "COM3"
BAUD_RATE = 115200
WARMUP_PACKETS = 50
MAX_BUFFER = 200


@dataclass(slots=True)
class DetectionResult:
    packet_type: int
    rssi: int
    anomaly: bool
    score_label: str


def open_serial(port: str = SERIAL_PORT, baud_rate: int = BAUD_RATE) -> serial.Serial:
    return serial.Serial(port, baud_rate, timeout=1)


def parse_packet_line(raw_line: str) -> Optional[list[int]]:
    if not raw_line or "," not in raw_line:
        return None

    try:
        values = [int(part.strip()) for part in raw_line.split(",")[:2]]
    except ValueError:
        return None

    if len(values) < 2:
        return None

    return values


def build_model(contamination: float) -> IsolationForest:
    return IsolationForest(contamination=contamination, random_state=42)


def detect_packet(data_buffer: list[list[int]], values: list[int], contamination: float) -> DetectionResult:
    packet_type, rssi = values
    anomaly_flag = False
    score_label = "WARMING UP"

    if len(data_buffer) > WARMUP_PACKETS:
        frame = pd.DataFrame(data_buffer[-100:], columns=["type", "rssi"])
        model = build_model(contamination)
        model.fit(frame)

        current_packet = pd.DataFrame([values], columns=["type", "rssi"])
        prediction = model.predict(current_packet)
        anomaly_flag = prediction[0] == -1
        score_label = "ANOMALY" if anomaly_flag else "SECURE"

    return DetectionResult(
        packet_type=packet_type,
        rssi=rssi,
        anomaly=anomaly_flag,
        score_label=score_label,
    )