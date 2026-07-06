"""CLI entry point for the RouteOpt Agent backend."""
from __future__ import annotations

import argparse
import json

from src.agent_workflow import run_routing_workflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RouteOpt Agent workflow on a scenario file.")
    parser.add_argument("scenario", help="Path to a local scenario file.")
    parser.add_argument("--time-limit", type=float, default=12.0, help="Maximum allowed time per driver.")
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    state = run_routing_workflow(args.scenario, time_limit=args.time_limit)
    if state.errors:
        raise SystemExit("\n".join(state.errors))

    if args.json:
        print(json.dumps(state.result, indent=2))
    else:
        print(state.explanation)
        print("\nRoutes:")
        for driver, route in state.result["routes"].items():
            print(f"  Driver {driver}: {route}")


if __name__ == "__main__":
    main()
