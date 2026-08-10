import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.agent import answer_question
from backend.bootstrap import main as bootstrap


def main() -> int:
    bootstrap()
    cases = json.loads((ROOT / "eval" / "test_questions.json").read_text(encoding="utf-8"))
    passed = 0
    for case in cases:
        result = answer_question(case["question"])
        text = result["answer"].lower()
        contains_ok = all(fragment.lower() in text for fragment in case["must_contain"])
        confidence_ok = result["confidence"]["level"] == case["expected_confidence"]
        ok = contains_ok and confidence_ok
        passed += int(ok)
        print(f"{'PASS' if ok else 'FAIL'} - {case['question']} [{result['confidence']['level']}]")
        if not ok:
            print(f"  answer: {result['answer']}")
    print(f"{passed}/{len(cases)} passing")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
