#!/usr/bin/env python3

import argparse
import hashlib
import os
import subprocess
import sys

import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST", "aws-0-us-east-1.pooler.supabase.com")
DB_PORT = os.environ.get("DB_PORT", "6543")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("SENSOR_DB_USER", "sensor_ingest.relglfpyctcldlbgsjdn")
DB_PASSWORD = os.environ.get("SENSOR_DB_PASSWORD")

if not DB_PASSWORD:
    sys.exit(
        "Falta SENSOR_DB_PASSWORD. Ponla en ingest/.env o expórtala:\n"
        "  export SENSOR_DB_PASSWORD='...'"
    )

TSHARK_FIELDS = [
    "frame.time_epoch",
    "ip.src",
    "ip.dst",
    "_ws.col.Protocol",
    "frame.len",
    "data.data",
]


def build_tshark_command(interface: str) -> list[str]:
    cmd = ["tshark", "-i", interface, "-l", "-n", "-T", "fields", "-E", "separator=|"]
    for field in TSHARK_FIELDS:
        cmd += ["-e", field]
    return cmd


def compute_payload_hash(data_hex: str, fallback_seed: str) -> str:
    raw = data_hex if data_hex else fallback_seed
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--interface", required=True, help="Interfaz a capturar (ver `tshark -D`)"
    )
    args = parser.parse_args()

    conninfo = (
        f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} "
        f"user={DB_USER} password={DB_PASSWORD}"
    )

    cmd = build_tshark_command(args.interface)
    print(f"[*] Ejecutando: {' '.join(cmd)}", file=sys.stderr)
    print("[*] Ctrl+C para detener.\n", file=sys.stderr)

    inserted = 0

    with psycopg.connect(conninfo, autocommit=True, prepare_threshold=None) as conn:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True) as proc:
            try:
                for line in proc.stdout:
                    parts = line.rstrip("\n").split("|")
                    if len(parts) < 5:
                        continue

                    ts_epoch, src_ip, dst_ip, protocol, length_str = parts[0:5]
                    data_hex = parts[5] if len(parts) > 5 else ""

                    if not src_ip or not dst_ip:
                        continue

                    try:
                        length = int(float(length_str)) if length_str else 0
                        ts = float(ts_epoch)
                    except ValueError:
                        continue

                    fallback_seed = f"{ts_epoch}:{src_ip}:{dst_ip}:{length_str}"
                    phash = compute_payload_hash(data_hex, fallback_seed)

                    conn.execute(
                        """
                        insert into public.network_logs
                            ("timestamp", src_ip, dst_ip, protocol, length, payload_hash)
                        values (to_timestamp(%s), %s, %s, %s, %s, %s)
                        """,
                        (ts, src_ip, dst_ip, protocol or "UNKNOWN", length, phash),
                    )
                    inserted += 1
                    print(f"[{inserted}] {src_ip} -> {dst_ip}  {protocol}  {length}B")
            except KeyboardInterrupt:
                print(f"\n[*] Detenido. {inserted} paquetes insertados.", file=sys.stderr)


if __name__ == "__main__":
    main()
