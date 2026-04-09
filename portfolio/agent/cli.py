import argparse
import logging

from .agent import Agent
from .lobster_skill import LobsterFetcherSkill
from .qt_annotator_skill import QtAnnotatorSkill


logging.basicConfig(level=logging.INFO, format="[portfolio-agent] %(levelname)s %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portfolio Agent CLI (local-first).")
    sub = parser.add_subparsers(dest="action", required=True)

    p1 = sub.add_parser("annotate-qt", help="Annotate a C++/Qt file with Doxygen-style comments.")
    p1.add_argument("--file", dest="file_path", required=True, help="Path to the .cpp/.h file.")
    p1.add_argument("--model", dest="model_name", default="gemma2:9b", help="Local Ollama model name.")

    p2 = sub.add_parser("harvest", help="Concurrent async harvesting demo (network I/O + limit).")
    p2.add_argument("--range", dest="target_range", type=int, required=True, help="Fetch IDs in [1..range].")
    p2.add_argument("--concurrency", dest="concurrency_limit", type=int, default=20, help="Concurrent workers.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    agent = Agent(
        qt_annotator=QtAnnotatorSkill(model_name=args.model_name if args.action == "annotate-qt" else "gemma2:9b"),
        lobster=LobsterFetcherSkill(concurrency_limit=args.concurrency_limit if args.action == "harvest" else 10),
    )

    if args.action == "annotate-qt":
        result = agent.run("annotate-qt", file_path=args.file_path)
        print("\n----- Annotated Result -----\n")
        print(result)
        print("\n------------------------------\n")
        return

    if args.action == "harvest":
        result = agent.run("harvest", target_range=args.target_range)
        print("\n----- Harvest Result (summary) -----\n")
        ok = sum(1 for r in result if r.get("status") == "success")
        print(f"Total={len(result)} Success={ok} Failed={len(result)-ok}")
        print("\nFirst 5 items:\n")
        for item in result[:5]:
            print(item)
        return


if __name__ == "__main__":
    main()

