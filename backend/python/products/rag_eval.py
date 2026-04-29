from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence, Tuple

from .rag import ask_the_expert, retrieve_relevant_chunks


RETRIEVAL_TEST_CASES: List[Dict[str, Any]] = [
    {
        "query": "What's the return policy for damaged items?",
        "expected_source": "return_policy.txt",
        "expected_terms": ["damaged", "refund", "replacement"],
    },
    {
        "query": "What is the warranty period for the Lego Castle?",
        "expected_source": "product_manual.txt",
        "expected_terms": ["warranty", "6 months"],
    },
    {
        "query": "When do vendors receive payment?",
        "expected_source": "vendor_faq.txt",
        "expected_terms": ["payment", "5 business days"],
    },
]


RAG_TEST_CASES: List[Dict[str, Any]] = [
    {
        "question": "What is the warranty period for the Lego Castle?",
        "expected_source": "product_manual.txt",
        "expected_terms": ["6 months"],
    },
    {
        "question": "What's the return policy for damaged items?",
        "expected_source": "return_policy.txt",
        "expected_terms": ["refund", "replacement"],
    },
]


def evaluate_retrieval(
    test_cases: Sequence[Dict[str, Any]] = RETRIEVAL_TEST_CASES,
    *,
    top_k: int = 3,
) -> Tuple[bool, Dict[str, Any]]:
    case_reports: List[Dict[str, Any]] = []
    passed = 0

    for case in test_cases:
        chunks = retrieve_relevant_chunks(str(case["query"]), top_k=top_k)
        sources = [chunk.source for chunk in chunks]
        combined_text = " ".join(chunk.content.lower() for chunk in chunks)
        expected_terms = [str(term).lower() for term in case["expected_terms"]]

        source_match = case["expected_source"] in sources
        terms_match = all(term in combined_text for term in expected_terms)
        ok = source_match and terms_match
        passed += int(ok)

        case_reports.append(
            {
                "query": case["query"],
                "expected_source": case["expected_source"],
                "sources": sources,
                "expected_terms": case["expected_terms"],
                "passed": ok,
            }
        )

    report = {
        "suite": "retrieval",
        "cases_total": len(test_cases),
        "cases_passed": passed,
        "pass_rate": passed / len(test_cases) if test_cases else 1.0,
        "cases": case_reports,
    }
    return passed == len(test_cases), report


def evaluate_rag(
    test_cases: Sequence[Dict[str, Any]] = RAG_TEST_CASES,
    *,
    top_k: int = 3,
) -> Tuple[bool, Dict[str, Any]]:
    case_reports: List[Dict[str, Any]] = []
    passed = 0

    for case in test_cases:
        result = ask_the_expert(str(case["question"]), top_k=top_k)
        sources = [source["source"] for source in result["sources"]]
        answer = str(result["answer"]).lower()
        expected_terms = [str(term).lower() for term in case["expected_terms"]]

        source_match = case["expected_source"] in sources
        answer_match = all(term in answer for term in expected_terms)
        ok = source_match and answer_match
        passed += int(ok)

        case_reports.append(
            {
                "question": case["question"],
                "answer": result["answer"],
                "expected_source": case["expected_source"],
                "sources": sources,
                "expected_terms": case["expected_terms"],
                "passed": ok,
            }
        )

    report = {
        "suite": "rag",
        "cases_total": len(test_cases),
        "cases_passed": passed,
        "pass_rate": passed / len(test_cases) if test_cases else 1.0,
        "cases": case_reports,
    }
    return passed == len(test_cases), report


def main() -> None:
    retrieval_ok, retrieval_report = evaluate_retrieval()
    rag_ok, rag_report = evaluate_rag()
    print(json.dumps([retrieval_report, rag_report], indent=2))
    raise SystemExit(0 if retrieval_ok and rag_ok else 1)


if __name__ == "__main__":
    main()
