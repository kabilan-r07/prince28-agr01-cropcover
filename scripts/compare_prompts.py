"""Score versioned question-router prompts on eval/prompt_testset.jsonl."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from cropcover.config import get_settings
from cropcover.db.llm_calls import make_recorder
from cropcover.db.session import make_engine, make_sessionmaker
from cropcover.llm.classify import LABELS, accuracy, classify, find_leaks
from cropcover.llm.gateway import LLMUnavailable, build_gateway
from cropcover.llm.prompts import read_prompt, versions

ROOT = Path(__file__).resolve().parents[1]


def load_rows(path: Path) -> list[dict[str, str]]:
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if len(rows) < 20:
        raise ValueError(f"test set needs at least 20 questions; found {len(rows)}")
    for n, row in enumerate(rows, 1):
        if set(row) != {"question", "label"} or row["label"] not in LABELS:
            raise ValueError(f"line {n}: expected question and label in {LABELS}")
    return rows


async def run(args: argparse.Namespace) -> int:
    settings = get_settings()
    engine = make_engine(settings)
    sessions = make_sessionmaker(engine)
    gateway = build_gateway(settings, recorder=make_recorder(sessions))
    cache_dir = ROOT / "eval" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    rows = load_rows(ROOT / "eval" / "prompt_testset.jsonl")
    names = versions(settings.prompts_dir, "classify")
    try:
        for name in names:
            prompt = read_prompt(settings.prompts_dir, name)
            if "TODO" in prompt:
                print(f"skipped {name}: the file still contains TODO")
                continue
            leaks = find_leaks(prompt, [r["question"] for r in rows])
            if leaks:
                print(f"LEAK in {name}: {leaks[0]}")
                continue
            scored, total_tokens, total_cost = [], 0, 0.0
            for row in rows:
                key = hashlib.sha256(f"{name}\0{prompt}\0{row['question']}".encode()).hexdigest()
                cache_file = cache_dir / f"{key}.json"
                if cache_file.exists():
                    result = json.loads(cache_file.read_text(encoding="utf-8"))
                else:
                    label, call = await classify(gateway, prompt, name, row["question"])
                    result = {
                        "got": label,
                        "tokens_in": call.tokens_in,
                        "cost_inr": call.cost_inr,
                    }
                    cache_file.write_text(json.dumps(result), encoding="utf-8")
                    await asyncio.sleep(60 / max(args.rpm, 1))
                total_tokens += result["tokens_in"]
                total_cost += result.get("cost_inr", 0.0)
                scored.append({**row, "got": result["got"]})
            correct = sum(x["got"] == x["label"] for x in scored)
            tokens_per_question = total_tokens / len(scored)
            print(
                f"{name}: {accuracy(scored):.0%} ({correct}/{len(scored)}), "
                f"input tokens/question={tokens_per_question:.1f}, cost=Rs {total_cost:.4f}"
            )
            print(
                "  missed:",
                "; ".join(
                    f"{i + 1}:{r['label']}->{r['got']} {r['question']}"
                    for i, r in enumerate(scored)
                    if r["got"] != r["label"]
                )
                or "none",
            )
    except LLMUnavailable as exc:
        print(f"stopped: no model can answer ({exc})")
        return 1
    finally:
        await gateway.aclose()
        await engine.dispose()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpm", type=int, default=12)
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
