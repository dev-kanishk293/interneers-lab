from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Sequence, Tuple

from .semantic_search import SemanticSearchIndex


EVAL_PRODUCTS: List[Dict[str, Any]] = [
    {
        "product_id": "lego_castle_001",
        "name": "Lego Castle Set",
        "description": "Interlocking building bricks and mini-figures for creative building and engineering play.",
        "category": "Toys",
        "brand": "LEGO",
    },
    {
        "product_id": "lego_city_002",
        "name": "Lego City Starter Kit",
        "description": "Build streets, vehicles, and structures with snap-together bricks for imaginative construction play.",
        "category": "Toys",
        "brand": "LEGO",
    },
    {
        "product_id": "wooden_blocks_003",
        "name": "Wooden Blocks Set",
        "description": "Stackable wooden pieces designed for building towers, shapes, and simple structures.",
        "category": "Toys",
        "brand": "PlayWood",
    },
    {
        "product_id": "soft_blocks_004",
        "name": "Soft Blocks for Babies",
        "description": "Soft foam blocks sized for small hands; safe texture and easy stacking for toddlers.",
        "category": "Baby & Toddler",
        "brand": "SoftSteps",
    },
    {
        "product_id": "plush_toy_005",
        "name": "Plush Bunny",
        "description": "Gentle plush toy with stitched features; comforting gift for toddlers and infants.",
        "category": "Baby & Toddler",
        "brand": "CuddleCo",
    },
    {
        "product_id": "baby_rattle_006",
        "name": "Baby Rattle",
        "description": "Lightweight rattle with soft grip; engages newborns with gentle sound and motion.",
        "category": "Baby & Toddler",
        "brand": "TinyTunes",
    },
    {
        "product_id": "teddy_bear_010",
        "name": "Teddy Bear",
        "description": "Classic stuffed bear with soft fabric and durable stitching.",
        "category": "Toys",
        "brand": "CuddleCo",
    },
    {
        "product_id": "action_figure_015",
        "name": "Action Figure",
        "description": "Poseable hero figure with accessories for pretend play.",
        "category": "Toys",
        "brand": "HeroWorks",
    },
    {
        "product_id": "puzzle_1000pc_020",
        "name": "1000-piece Puzzle",
        "description": "Challenging jigsaw puzzle for teens and adults; detailed artwork.",
        "category": "Games",
        "brand": "PuzzlePro",
    },
    {
        "product_id": "teen_board_game_025",
        "name": "Strategy Board Game",
        "description": "Competitive strategy board game designed for older kids and teens.",
        "category": "Games",
        "brand": "BoardMaster",
    },
]


SEARCH_TEST_CASES: List[Dict[str, Any]] = [
    {
        "query": "construction toys",
        "relevant_products": ["lego_castle_001", "lego_city_002", "wooden_blocks_003"],
        "irrelevant_products": ["teddy_bear_010", "action_figure_015"],
    },
    {
        "query": "gifts for toddlers",
        "relevant_products": ["soft_blocks_004", "plush_toy_005", "baby_rattle_006"],
        "irrelevant_products": ["puzzle_1000pc_020", "teen_board_game_025"],
    },
]

def evaluate_semantic_search(
    *,
    products: Sequence[Dict[str, Any]] = EVAL_PRODUCTS,
    test_cases: Sequence[Dict[str, Any]] = SEARCH_TEST_CASES,
    model_name: str = "all-MiniLM-L6-v2",
    top_k: int = 5,
) -> Tuple[bool, Dict[str, Any]]:
    index = SemanticSearchIndex(products, model_name=model_name)

    case_reports: List[Dict[str, Any]] = []
    passed = 0

    for case in test_cases:
        query = str(case["query"])
        relevant = [str(pid) for pid in case.get("relevant_products", [])]
        irrelevant = [str(pid) for pid in case.get("irrelevant_products", [])]

        results = index.search(query, top_k=top_k)
        ranked = [str(result.product.get("product_id")) for result in results]

        relevant_set = set(relevant)
        irrelevant_set = set(irrelevant)

        relevant_in_top_k = [pid for pid in ranked if pid in relevant_set]
        top_guard_k = min(max(3, len(relevant)), top_k) if top_k > 0 else 0
        ranked_guard = ranked[:top_guard_k]
        irrelevant_in_top_guard = [pid for pid in ranked_guard if pid in irrelevant_set]

        missing_relevant = [pid for pid in relevant if pid not in set(ranked)]

        ok = (not missing_relevant) and (not irrelevant_in_top_guard)
        passed += int(ok)

        case_reports.append(
            {
                "query": query,
                "top_k": top_k,
                "top_guard_k": top_guard_k,
                "ranked_product_ids": ranked,
                "relevant_in_top_k": relevant_in_top_k,
                "missing_relevant": missing_relevant,
                "irrelevant_in_top_guard": irrelevant_in_top_guard,
                "passed": ok,
            }
        )

    summary = {
        "model_name": model_name,
        "top_k": top_k,
        "cases_total": len(test_cases),
        "cases_passed": passed,
        "pass_rate": (passed / len(test_cases)) if test_cases else 1.0,
        "cases": case_reports,
    }
    return passed == len(test_cases), summary


def main() -> None:
    ok, report = evaluate_semantic_search()
    print(json.dumps(report, indent=2, sort_keys=False))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
