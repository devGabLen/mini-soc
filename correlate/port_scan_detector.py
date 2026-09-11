#!/usr/bin/env python3

import argparse
import os
import time
from datetime import datetime, timezone

import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST", "aws-0-us-east-1.pooler.supabase.com")
DB_PORT = os.environ.get("DB_PORT", "6543")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("CORRELATION_DB_USER", "correlation_engine.relglfpyctcldlbgsjdn")
DB_PASSWORD = os.environ.get("CORRELATION_DB_PASSWORD")

MIN_CONNECTIONS = 50
MAX_WINDOW_SECONDS = 10

def severity_for(count: int) -> int:
    if count >= 400:
        return 4
    if count >= 150:
        return 3
    if count >= MIN_CONNECTIONS:
        return 2
    return 1


def get_conninfo() -> str:
    if not DB_PASSWORD:
        raise SystemExit(
            "Falta CORRELATION_DB_PASSWORD. Ponla en correlate/.env o expórtala."
        )
    return (
        f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} "
        f"user={DB_USER} password={DB_PASSWORD}"
    )


def run_once(conn: psycopg.Connection) -> int:
    checkpoint = conn.execute(
        "select last_processed_at from private.correlation_runs where id = true"
    ).fetchone()[0]

    groups = conn.execute(
        """
        select src_ip, dst_ip, count(*) as cnt,
               min("timestamp") as first_ts, max("timestamp") as last_ts
        from public.network_logs
        where "timestamp" > %s
          and protocol = 'TCP'
        group by src_ip, dst_ip
        having count(*) >= %s
           and extract(epoch from (max("timestamp") - min("timestamp"))) <= %s
        """,
        (checkpoint, MIN_CONNECTIONS, MAX_WINDOW_SECONDS),
    ).fetchall()

    alerts_created = 0

    for src_ip, dst_ip, cnt, first_ts, last_ts in groups:
        conn.execute(
            """
            insert into public.alerts
                (category, mitre_tactic, severity, description, src_ip, dst_ip, occurred_at)
            values (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "reconocimiento",
                "TA0043",
                severity_for(cnt),
                f"Posible escaneo de puertos: {cnt} conexiones TCP de {src_ip} "
                f"hacia {dst_ip} en {(last_ts - first_ts).total_seconds():.2f}s",
                src_ip,
                dst_ip,
                first_ts,
            ),
        )
        alerts_created += 1
        print(f"[ALERTA] {src_ip} -> {dst_ip}: {cnt} conexiones -> severidad {severity_for(cnt)}")

    newest = conn.execute(
        'select max("timestamp") from public.network_logs where "timestamp" > %s',
        (checkpoint,),
    ).fetchone()[0]

    if newest is not None:
        conn.execute(
            "update private.correlation_runs set last_processed_at = %s where id = true",
            (newest,),
        )

    return alerts_created


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Correr en bucle continuo")
    parser.add_argument("--interval", type=int, default=10, help="Segundos entre corridas (--loop)")
    args = parser.parse_args()

    conninfo = get_conninfo()

    with psycopg.connect(conninfo, autocommit=True, prepare_threshold=None) as conn:
        if args.loop:
            print(f"[*] Corriendo en bucle cada {args.interval}s. Ctrl+C para detener.")
            try:
                while True:
                    n = run_once(conn)
                    if n:
                        print(f"[*] {n} alerta(s) nueva(s) - {datetime.now(timezone.utc).isoformat()}")
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n[*] Detenido.")
        else:
            n = run_once(conn)
            print(f"[*] Corrida única completa. {n} alerta(s) nueva(s).")


if __name__ == "__main__":
    main()
