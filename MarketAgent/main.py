#!/usr/bin/env python3
import sys
import os

def main():
    print("\nMarketAgent — Autonomous SEO & Marketing Assistant")
    print("=" * 50)

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("\nHow would you like to run MarketAgent?")
        print("  1  CLI (terminal dashboard)")
        print("  2  Web UI (browser dashboard at localhost:8080)")
        choice = input("\nChoice [1/2]: ").strip()
        mode = "cli" if choice == "1" else "web"

    if mode in ("cli", "1"):
        from ui.cli import run_cli
        run_cli()
    else:
        from ui.web.app import run_web
        print("\nStarting web UI at http://localhost:8080")
        print("Press Ctrl+C to stop.\n")
        run_web()


if __name__ == "__main__":
    main()
