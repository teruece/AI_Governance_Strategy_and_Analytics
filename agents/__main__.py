"""Run a synthetic KPI or data-quality agent scenario."""

import argparse
import json
import os

from . import kpi, quality
from .openai_planner import OpenAIPlanner
from .runtime import ScriptedPlanner, run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("kpi", "quality"))
    parser.add_argument("--scenario", choices=("normal", "blocked"), default="normal")
    parser.add_argument("--backend", choices=("scripted", "openai"), default="scripted")
    parser.add_argument("--model", help="Responses API model with function calling")
    args = parser.parse_args()

    case = {"kpi": kpi, "quality": quality}[args.case]
    tools = case.tools(args.scenario)
    if args.backend == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not args.model or not api_key:
            parser.error("--backend openai requires --model and OPENAI_API_KEY")
        planner = OpenAIPlanner(
            tools, case.INSTRUCTIONS, case.question(args.scenario), args.model, api_key
        )
    else:
        if args.model:
            parser.error("--model requires --backend openai")
        planner = ScriptedPlanner(case.script(args.scenario))

    outcome = run(tools, planner, case.render)
    print(json.dumps(
        {"case": args.case, "scenario": args.scenario, "backend": args.backend, **outcome},
        indent=2,
    ))
    return 2 if outcome["status"] == "STOPPED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
