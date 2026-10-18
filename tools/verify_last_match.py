"""Verify a finished match audit and print a concise diagnostic report.

Example:
  python tools/verify_last_match.py
  python tools/verify_last_match.py "C:\\Users\\...\\AuctionHammer-OSTATNI-MECZ.json"

Does not execute commands from the JSON as Python code. Only the known public
v19 Match commands are replayed inside a fresh deterministic match.
"""
from __future__ import annotations
import sys
from pathlib import Path
import argparse
import json

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game.core.engine import Match
from game.core.audit import audit_path,read_report,verify_replay


def main():
    p=argparse.ArgumentParser(description="AuctionHammer — weryfikacja ostatniego meczu")
    p.add_argument("file",nargs="?",type=Path,default=audit_path())
    p.add_argument("--skip-replay",action="store_true",
                   help="Sprawdź SHA-256 bez ponownego przeliczania silnika")
    args=p.parse_args()
    data=read_report(args.file)
    print("AUCTIONHAMMER · RAPORT AUDYTU")
    print("Game Master:",data["specification"])
    print("Zapis kompletny:", "TAK" if data["complete_from_start"] else "NIE")
    print("Ziarno losowe:",data["seed"])
    print("Zwycięzca:",data["summary"]["winner"])
    print("Rundy:",data["summary"]["rounds"])
    print("Komendy:",data["summary"]["action_commands"])
    print("Nieudane próby:",data["summary"]["failed_commands"])
    print("Zdarzenia:",data["summary"]["events"])
    print("Spójność pliku: OK (SHA-256)")
    if args.skip_replay or not data["complete_from_start"]:
        print("Odtworzenie silnika: POMINIĘTE")
    else:
        verify_replay(data,lambda seed,auctions_enabled=False:
                      Match(seed,audit_enabled=True,auctions_enabled=auctions_enabled))
        print("Odtworzenie silnika: OK — wszystkie stany i zdarzenia zgodne")
    print("Plik:",args.file)


if __name__=="__main__":
    try:
        main()
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as exc:
        print("BŁĄD AUDYTU:",exc,file=sys.stderr)
        sys.exit(1)
