"""
Deterministyczny benchmark algorytmów sterowania windą.
Uruchomienie: python benchmark.py
Uruchomienie z konkretnym scenariuszem: python benchmark.py scenarios/morning_rush.json
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from simulation.building import Building
from simulation.passenger import Passenger, reset_id_counter
from metrics.collector import MetricsCollector
from algorithms import ALGORITHMS
from algorithms.scan import SCANDispatcher

NUM_ELEVATORS = 2
DT = 0.05          # krok symulacji (s)
MAX_SIM_TIME = 600  # limit czasowy (s) — ochrona przed infinite loop


def make_dispatcher(name: str, num_floors: int):
    cls = ALGORITHMS[name]
    return cls(num_floors) if name == "SCAN" else cls()


def load_scenario(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_scenario(scenario: dict, algo_name: str) -> dict:
    """Uruchamia jeden scenariusz z jednym algorytmem. Zwraca metryki."""
    reset_id_counter()
    num_floors = scenario["num_floors"]
    passengers_data = scenario["passengers"]

    collector = MetricsCollector()
    dispatcher = make_dispatcher(algo_name, num_floors)
    building = Building(num_floors, NUM_ELEVATORS, dispatcher, collector)

    # Przygotuj listę pasażerów posortowaną po czasie przybycia
    schedule = sorted(passengers_data, key=lambda p: p["arrival_time"])
    schedule_idx = 0
    total_passengers = len(schedule)

    sim_time = 0.0
    while sim_time <= MAX_SIM_TIME:
        # Dodaj pasażerów których czas przybycia minął
        while schedule_idx < total_passengers and schedule[schedule_idx]["arrival_time"] <= sim_time:
            entry = schedule[schedule_idx]
            p = Passenger(
                origin_floor=entry["origin"],
                destination_floor=entry["destination"],
                arrival_time=entry["arrival_time"],
            )
            building.add_passenger(p)
            schedule_idx += 1

        building.update(DT, sim_time)
        collector.tick(sim_time)
        sim_time += DT
        sim_time = round(sim_time, 6)  # unikamy błędów zmiennoprzecinkowych

        # Zakończ gdy wszyscy pasażerowie zostali obsłużeni
        if collector.total_served == total_passengers and schedule_idx == total_passengers:
            break

    return {
        "algo": algo_name,
        "total": total_passengers,
        "served": collector.total_served,
        "avg_wait": collector.avg_wait_time,
        "max_wait": collector.max_wait_time,
        "avg_trip": collector.avg_trip_time,
        "avg_total": collector.avg_total_time,
        "throughput": collector.throughput,
        "sim_time": sim_time,
    }


def print_results(scenario: dict, results: list[dict]) -> None:
    name = scenario["name"]
    desc = scenario["description"]
    n_floors = scenario["num_floors"]
    n_pass = len(scenario["passengers"])

    print()
    print("=" * 72)
    print(f"  Scenariusz: {name}")
    print(f"  {desc}")
    print(f"  Budynek: {n_floors} pięter, {NUM_ELEVATORS} windy, {n_pass} pasażerów")
    print("=" * 72)
    header = f"{'Algorytm':<8}  {'Obsłuż.':<8}  {'Śr.czek.':<10}  {'Maks.czek.':<11}  {'Śr.jazda':<10}  {'Śr.total':<10}  {'Czas sim.':<10}"
    print(header)
    print("-" * 72)

    # Znajdź najlepszą wartość dla każdej metryki (do kolorowania)
    best_wait = min(r["avg_wait"] for r in results)
    best_max  = min(r["max_wait"] for r in results)
    best_trip = min(r["avg_trip"] for r in results)

    for r in results:
        mark_wait  = " *" if r["avg_wait"] == best_wait else "  "
        mark_max   = " *" if r["max_wait"] == best_max  else "  "
        mark_trip  = " *" if r["avg_trip"] == best_trip else "  "
        print(
            f"{r['algo']:<8}  "
            f"{r['served']}/{r['total']:<5}   "
            f"{r['avg_wait']:>6.2f}s{mark_wait}  "
            f"{r['max_wait']:>7.2f}s{mark_max}    "
            f"{r['avg_trip']:>6.2f}s{mark_trip}  "
            f"{r['avg_total']:>7.2f}s    "
            f"{r['sim_time']:>6.1f}s"
        )
    print("-" * 72)
    print("  * = najlepszy wynik w danej kategorii")
    print()


def run_all(scenario_path: str) -> None:
    scenario = load_scenario(scenario_path)
    results = []
    for algo in ALGORITHMS:
        r = run_scenario(scenario, algo)
        results.append(r)
    print_results(scenario, results)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        paths = sys.argv[1:]
    else:
        # Domyślnie uruchom oba scenariusze
        base = Path(__file__).parent / "scenarios"
        paths = [
            str(base / "morning_rush.json"),
            str(base / "residential.json"),
        ]

    for path in paths:
        run_all(path)
