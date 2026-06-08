#!/usr/bin/env python3
"""
Stress Test - ONPE Resultados Segunda Vuelta
Mide cuántas peticiones por minuto acepta el endpoint.
Uso: python3 stress_test_onpe.py [--concurrency N] [--duration S] [--rps N]
"""

import argparse
import asyncio
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

import aiohttp

# ─── Configuración del endpoint ────────────────────────────────────────────────
URL = (
    "https://resultadosegundavuelta.onpe.gob.pe/presentacion-backend/"
    "resumen-general/totales"
    "?idEleccion=10&tipoFiltro=ubigeo_nivel_03"
    "&idAmbitoGeografico=1&idUbigeoDepartamento=030000"
    "&idUbigeoProvincia=030400&idUbigeoDistrito=030404"
)

HEADERS = {
    "accept": "*/*",
    "accept-language": "es,en;q=0.9,en-US;q=0.8",
    "content-type": "application/json",
    "priority": "u=1, i",
    "referer": "https://resultadosegundavuelta.onpe.gob.pe/main/resumen",
    "sec-ch-ua": '"Opera";v="131", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36 OPR/131.0.0.0"
    ),
}

COOKIES = {
    "_ga": "GA1.1.1192358612.1776099130",
}


# ─── Estructuras de resultado ───────────────────────────────────────────────────
@dataclass
class RequestResult:
    status: int
    latency_ms: float
    timestamp: float
    error: str = ""


@dataclass
class Stats:
    results: list = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    def add(self, r: RequestResult):
        self.results.append(r)

    def summary(self) -> dict:
        if not self.results:
            return {}
        elapsed = time.time() - self.start_time
        total = len(self.results)
        ok = [r for r in self.results if r.status == 200]
        errors = [r for r in self.results if r.status != 200 or r.error]
        # Latencias de TODAS las peticiones con respuesta (status>0)
        all_lat = [r.latency_ms for r in self.results if r.latency_ms > 0]
        ok_lat = [r.latency_ms for r in ok] if ok else []
        latencies = all_lat if all_lat else [0]

        status_count = defaultdict(int)
        error_types = defaultdict(int)
        for r in self.results:
            status_count[r.status if r.status else "conn_error"] += 1
            if r.error:
                short = r.error.split(":")[0]
                error_types[short] += 1

        return {
            "total_requests": total,
            "successful": len(ok),
            "failed": len(errors),
            "elapsed_s": round(elapsed, 2),
            "req_per_sec": round(total / elapsed, 2),
            "req_per_min": round((total / elapsed) * 60, 1),
            "avg_latency_ms": round(statistics.mean(latencies), 1),
            "median_latency_ms": round(statistics.median(latencies), 1),
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 1),
            "max_latency_ms": round(max(latencies), 1),
            "min_latency_ms": round(min(latencies), 1),
            "ok_avg_latency_ms": round(statistics.mean(ok_lat), 1) if ok_lat else None,
            "status_codes": dict(status_count),
            "error_types": dict(error_types),
        }


# ─── Worker asíncrono ───────────────────────────────────────────────────────────
async def worker(
    session: aiohttp.ClientSession, stats: Stats, stop_event: asyncio.Event
):
    while not stop_event.is_set():
        t0 = time.perf_counter()
        status, error = 0, ""
        try:
            async with session.get(
                URL,
                headers=HEADERS,
                cookies=COOKIES,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                status = resp.status
                await resp.read()
        except asyncio.TimeoutError:
            status, error = 0, "timeout"
        except aiohttp.ClientConnectorError as e:
            status, error = 0, f"connection_error: {e}"
        except Exception as e:
            status, error = 0, str(e)
        latency_ms = (time.perf_counter() - t0) * 1000
        stats.add(
            RequestResult(
                status=status, latency_ms=latency_ms, timestamp=time.time(), error=error
            )
        )


# ─── Modo rate-limited (peticiones/seg fijo) ────────────────────────────────────
async def rate_limited_run(rps: int, duration: int, stats: Stats):
    interval = 1.0 / rps
    stop_event = asyncio.Event()
    connector = aiohttp.TCPConnector(limit=rps + 10, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:

        async def sender():
            t_end = time.time() + duration
            while time.time() < t_end:
                asyncio.create_task(worker_once(session, stats))
                await asyncio.sleep(interval)
            stop_event.set()

        async def worker_once(s, st):
            await worker.__wrapped__(s, st, asyncio.Event())  # one-shot

        # Redefine como one-shot para este modo
        async def fire_once():
            t0 = time.perf_counter()
            status, error = 0, ""
            try:
                async with session.get(
                    URL,
                    headers=HEADERS,
                    cookies=COOKIES,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    status = resp.status
                    await resp.read()
            except asyncio.TimeoutError:
                status, error = 0, "timeout"
            except Exception as e:
                status, error = 0, str(e)
            latency_ms = (time.perf_counter() - t0) * 1000
            stats.add(
                RequestResult(
                    status=status,
                    latency_ms=latency_ms,
                    timestamp=time.time(),
                    error=error,
                )
            )

        t_end = time.time() + duration
        while time.time() < t_end:
            asyncio.create_task(fire_once())
            await asyncio.sleep(interval)
        # Espera que terminen las últimas peticiones
        await asyncio.sleep(2)


# ─── Modo concurrencia fija ─────────────────────────────────────────────────────
async def concurrency_run(concurrency: int, duration: int, stats: Stats):
    stop_event = asyncio.Event()
    connector = aiohttp.TCPConnector(limit=concurrency + 5, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            asyncio.create_task(worker(session, stats, stop_event))
            for _ in range(concurrency)
        ]
        await asyncio.sleep(duration)
        stop_event.set()
        await asyncio.gather(*tasks, return_exceptions=True)


# ─── Impresión de progreso ──────────────────────────────────────────────────────
def print_progress(stats: Stats, interval: int = 5):
    s = stats.summary()
    if not s:
        return
    print(
        f"  [{datetime.now().strftime('%H:%M:%S')}] "
        f"Reqs: {s['total_requests']:>5} | "
        f"OK: {s['successful']:>5} | "
        f"Err: {s['failed']:>4} | "
        f"RPS: {s['req_per_sec']:>6.1f} | "
        f"RPM: {s['req_per_min']:>7.1f} | "
        f"Lat avg: {s['avg_latency_ms']:>6.0f}ms"
    )


# ─── Impresión de resumen final ─────────────────────────────────────────────────
def print_summary(stats: Stats, mode: str):
    s = stats.summary()
    print("\n" + "═" * 60)
    print("  RESULTADOS FINALES — ONPE Stress Test")
    print("═" * 60)
    print(f"  Modo:                {mode}")
    print(f"  Duración real:       {s['elapsed_s']} seg")
    print(f"  Total peticiones:    {s['total_requests']}")
    print(f"  Exitosas (200):      {s['successful']}")
    print(f"  Fallidas:            {s['failed']}")
    print("  ─────────────────────────────────────")
    print(f"  ✅ Req/segundo:      {s['req_per_sec']}")
    print(f"  ✅ Req/minuto est.:  {s['req_per_min']}")
    print("  ─────────────────────────────────────")
    ok_lat_str = (
        f"{s['ok_avg_latency_ms']} ms"
        if s.get("ok_avg_latency_ms")
        else "N/A (sin 200s)"
    )
    print(f"  Latencia promedio:   {s['avg_latency_ms']} ms  (solo 200s: {ok_lat_str})")
    print(f"  Latencia mediana:    {s['median_latency_ms']} ms")
    print(f"  Latencia p95:        {s['p95_latency_ms']} ms")
    print(f"  Latencia máxima:     {s['max_latency_ms']} ms")
    print("  ─────────────────────────────────────")
    print(f"  Códigos HTTP:        {s['status_codes']}")
    if s.get("error_types"):
        print(f"  Tipos de error:      {s['error_types']}")
    print("═" * 60)

    # Interpretación
    rpm = s["req_per_min"]
    err_rate = s["failed"] / max(s["total_requests"], 1) * 100
    print("\n  📊 INTERPRETACIÓN:")
    if err_rate > 20:
        print(
            f"  ⚠️  Tasa de error alta ({err_rate:.1f}%) — el servidor está saturado o bloqueando."
        )
    elif err_rate > 5:
        print(
            f"  ⚠️  Tasa de error moderada ({err_rate:.1f}%) — cerca del límite de capacidad."
        )
    else:
        print(f"  ✅ Tasa de error baja ({err_rate:.1f}%) — el servidor responde bien.")

    if rpm < 60:
        print("  ℹ️  Throughput bajo (<60 RPM). Posible rate-limit o latencia alta.")
    elif rpm < 300:
        print("  ℹ️  Throughput moderado. Servidor estable en este nivel.")
    else:
        print(f"  ✅ Alto throughput ({rpm:.0f} RPM). Sin señales de throttling.")
    print()


# ─── Punto de entrada ───────────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(
        description="Stress Test para ONPE Resultados Segunda Vuelta"
    )
    parser.add_argument(
        "--mode",
        choices=["concurrent", "rps"],
        default="concurrent",
        help="concurrent = N workers simultáneos | rps = N peticiones/seg fijas",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Número de workers concurrentes (modo concurrent, default=10)",
    )
    parser.add_argument(
        "--rps",
        type=int,
        default=5,
        help="Peticiones por segundo (modo rps, default=5)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Duración de la prueba en segundos (default=30)",
    )
    args = parser.parse_args()

    stats = Stats()

    print("═" * 60)
    print("  ONPE Stress Test — Resultados Segunda Vuelta")
    print("═" * 60)
    print(f"  URL:         {URL[:60]}...")
    print(f"  Modo:        {args.mode}")
    if args.mode == "concurrent":
        print(f"  Concurrencia:{args.concurrency} workers simultáneos")
    else:
        print(f"  Rate:        {args.rps} peticiones/seg")
    print(f"  Duración:    {args.duration} seg")
    print("─" * 60)
    print("  Iniciando prueba...\n")

    # Tarea de progreso cada 5 seg
    async def progress_loop():
        while True:
            await asyncio.sleep(5)
            print_progress(stats)

    prog_task = asyncio.create_task(progress_loop())

    try:
        if args.mode == "concurrent":
            await concurrency_run(args.concurrency, args.duration, stats)
        else:
            await rate_limited_run(args.rps, args.duration, stats)
    finally:
        prog_task.cancel()

    mode_str = (
        f"{args.concurrency} workers concurrentes"
        if args.mode == "concurrent"
        else f"{args.rps} req/s fijos"
    )
    print_summary(stats, mode_str)


if __name__ == "__main__":
    asyncio.run(main())
