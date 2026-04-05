import time

from sentinel_core import MAX_BUFFER, SERIAL_PORT, detect_packet, open_serial, parse_packet_line


def main() -> None:
    try:
        ser = open_serial()
        print("--- Security Sentinel Brain Active ---")
    except Exception as exc:
        print(f"Connection Error: {exc}")
        return

    data_buffer: list[list[int]] = []
    contamination = 0.03

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
            if result.anomaly:
                print(f"⚠️  ANOMALY DETECTED | Pkt: {result.packet_type} | RSSI: {result.rssi}")
            else:
                print(f"✅ SYSTEM SECURE   | Pkt: {result.packet_type} | RSSI: {result.rssi}")

        except KeyboardInterrupt:
            print("Stopping Brain...")
            break
        except Exception:
            continue


if __name__ == "__main__":
    main()