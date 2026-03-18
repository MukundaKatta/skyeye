"""CLI for skyeye."""
import sys, json, argparse
from .core import Skyeye

def main():
    parser = argparse.ArgumentParser(description="SkyEye — Drone Inspection Analyzer. AI analysis of drone inspection footage for infrastructure defects.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Skyeye()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.analyze(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"skyeye v0.1.0 — SkyEye — Drone Inspection Analyzer. AI analysis of drone inspection footage for infrastructure defects.")

if __name__ == "__main__":
    main()
