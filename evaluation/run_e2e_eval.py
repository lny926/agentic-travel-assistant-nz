import csv
import time
import uuid
from pathlib import Path

import requests

from evaluation.e2e_test_cases import (
    E2E_TEST_CASES
)


API_URL = (
    "http://127.0.0.1:8000/chat"
)

RESULTS_PATH = (
    Path(__file__).resolve().parent
    / "planner_results.csv"
)


def normalize_list(values):
    return {
        str(value).strip().lower()
        for value in values
    }


def run_evaluation():

    results = []

    total = len(E2E_TEST_CASES)

    routing_correct_count = 0
    source_correct_count = 0
    successful_count = 0

    print(
        "\n"
        "========================================"
    )

    print(
        "END-TO-END EVALUATION"
    )

    print(
        "========================================"
    )

    for index, test_case in enumerate(
        E2E_TEST_CASES,
        start=1
    ):

        print(
            f"\n[{index}/{total}] "
            f"{test_case['id']}"
        )

        print(
            "Question:",
            test_case["question"]
        )

        session_id = str(
            uuid.uuid4()
        )

        start_time = (
            time.perf_counter()
        )

        error = ""

        try:

            response = requests.post(
                API_URL,
                json={
                    "question": (
                        test_case["question"]
                    ),
                    "session_id": session_id
                },
                timeout=180
            )

            response.raise_for_status()

            elapsed = (
                time.perf_counter()
                - start_time
            )

            data = response.json()

            answer = data.get(
                "answer",
                ""
            )

            actual_services = data.get(
                "services",
                []
            )

            actual_sources = data.get(
                "sources",
                []
            )

            # ---------------------------------
            # Routing check
            # ---------------------------------

            expected_services = (
                normalize_list(
                    test_case[
                        "expected_services"
                    ]
                )
            )

            actual_service_set = (
                normalize_list(
                    actual_services
                )
            )

            routing_correct = (
                expected_services
                == actual_service_set
            )

            # ---------------------------------
            # Source check
            # ---------------------------------

            expected_sources = (
                test_case.get(
                    "expected_sources",
                    []
                )
            )

            actual_source_set = (
                normalize_list(
                    actual_sources
                )
            )

            source_correct = all(
                expected_source.lower()
                in actual_source_set
                for expected_source
                in expected_sources
            )

            # ---------------------------------
            # Basic response check
            # ---------------------------------

            answer_valid = (
                isinstance(answer, str)
                and len(answer.strip()) > 20
            )

            successful = (
                routing_correct
                and source_correct
                and answer_valid
            )

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - start_time
            )

            answer = ""
            actual_services = []
            actual_sources = []

            routing_correct = False
            source_correct = False
            answer_valid = False
            successful = False

            error = str(exc)

        if routing_correct:
            routing_correct_count += 1

        if source_correct:
            source_correct_count += 1

        if successful:
            successful_count += 1

        print(
            "Services:",
            actual_services
        )

        print(
            "Sources: ",
            actual_sources
        )

        print(
            f"Routing: "
            f"{'PASS' if routing_correct else 'FAIL'}"
        )

        print(
            f"Sources: "
            f"{'PASS' if source_correct else 'FAIL'}"
        )

        print(
            f"Answer:  "
            f"{'PASS' if answer_valid else 'FAIL'}"
        )

        print(
            f"Time:    "
            f"{elapsed:.1f}s"
        )

        results.append(
            {
                "id": test_case["id"],
                "category": (
                    test_case["category"]
                ),
                "question": (
                    test_case["question"]
                ),
                "expected_services": ", ".join(
                    test_case[
                        "expected_services"
                    ]
                ),
                "actual_services": ", ".join(
                    actual_services
                ),
                "expected_sources": ", ".join(
                    test_case.get(
                        "expected_sources",
                        []
                    )
                ),
                "actual_sources": ", ".join(
                    actual_sources
                ),
                "routing_correct": (
                    routing_correct
                ),
                "source_correct": (
                    source_correct
                ),
                "answer_valid": answer_valid,
                "successful": successful,
                "response_time": round(
                    elapsed,
                    2
                ),
                "answer": answer,
                "error": error
            }
        )

    # =====================================================
    # Summary
    # =====================================================

    routing_accuracy = (
        routing_correct_count
        / total
        * 100
    )

    source_accuracy = (
        source_correct_count
        / total
        * 100
    )

    success_rate = (
        successful_count
        / total
        * 100
    )

    print(
        "\n\n"
        "========================================"
    )

    print(
        "END-TO-END RESULTS"
    )

    print(
        "========================================"
    )

    print(
        f"Routing accuracy: "
        f"{routing_correct_count}/{total} "
        f"({routing_accuracy:.1f}%)"
    )

    print(
        f"Source accuracy:  "
        f"{source_correct_count}/{total} "
        f"({source_accuracy:.1f}%)"
    )

    print(
        f"Successful cases: "
        f"{successful_count}/{total} "
        f"({success_rate:.1f}%)"
    )

    # =====================================================
    # Save results
    # =====================================================

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        RESULTS_PATH,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "id",
                "category",
                "question",
                "expected_services",
                "actual_services",
                "expected_sources",
                "actual_sources",
                "routing_correct",
                "source_correct",
                "answer_valid",
                "successful",
                "response_time",
                "answer",
                "error"
            ]
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    print(
        "\nResults saved to:"
    )

    print(
        RESULTS_PATH
    )


if __name__ == "__main__":
    run_evaluation()