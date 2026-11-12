"""Three independent, offline artifact commands."""

import argparse
from pathlib import Path

from .pipeline import generate
from .report import report_file
from .scoring import score_file


def main():
    parser = argparse.ArgumentParser(description="CIB synthetic development fixture workflow")
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture", help="produce immutable scripted raw records")
    fixture.add_argument("--output", type=Path, required=True)
    score = commands.add_parser("score", help="score saved raw records, without response production")
    score.add_argument("--raw", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    report = commands.add_parser("report", help="render saved records and scores")
    report.add_argument("--raw", type=Path, required=True)
    report.add_argument("--scores", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "fixture":
            generate(args.output)
        elif args.command == "score":
            score_file(args.raw, args.output)
        else:
            report_file(args.raw, args.scores, args.output)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"cib: {error}\n")
    print(args.output)


if __name__ == "__main__":
    main()
