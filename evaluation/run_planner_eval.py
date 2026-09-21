import csv
from collections import defaultdict
from pathlib import Path

from evaluation.test_cases import (
    TEST_CASES
)

from src.graph.planner import (
    plan_request
)


RESULTS_PATH = (
    Path(__file__).resolve().parent
    / "planner_results.csv"
)


def normalize_services(services):
    """
    Compare services without caring
    about their order.
    """

    return set(
        str(service).strip().lower()
        for service in services
    )


def run_evaluation():

    results = []

    total = len(TEST_CASES)
    correct_count = 0

    category_stats = defaultdict(
        lambda: {
            "total": 0,
            "correct": 0
        }
    )

    print(
        "\n"
        "========================================"
    )

    print(
        "PLANNER ROUTING EVALUATION"
    )

    print(
        "========================================"
    )

    for index, test_case in enumerate(
        TEST_CASES,
        start=1
    ):

        question = (
            test_case["question"]
        )

        history = (
            test_case.get(
                "history",
                ""
            )
        )

        expected_services = (
            test_case[
                "expected_services"
            ]
        )

        print(
            f"\n[{index}/{total}] "
            f"{test_case['id']}"
        )

        print(
            "Question:",
            question
        )

        try:

            plan = plan_request(
                question=question,
                conversation_history=history
            )

            actual_services = (
                plan.get(
                    "services",
                    []
                )
            )

            expected_set = normalize_services(
                expected_services
            )

            actual_set = normalize_services(
                actual_services
            )

            correct = (
                expected_set
                == actual_set
            )

            error = ""

        except Exception as exc:

            actual_services = []

            correct = False

            error = str(exc)

        if correct:

            correct_count += 1

            status = "PASS"

        else:

            status = "FAIL"

        category = (
            test_case["category"]
        )

        category_stats[
            category
        ]["total"] += 1

        if correct:

            category_stats[
                category
            ]["correct"] += 1

        print(
            "Expected:",
            expected_services
        )

        print(
            "Actual:  ",
            actual_services
        )

        print(
            "Result:  ",
            status
        )

        if error:

            print(
                "Error:",
                error
            )

        results.append(
            {
                "id": (
                    test_case["id"]
                ),

                "category": category,

                "question": question,

                "expected_services": (
                    ", ".join(
                        expected_services
                    )
                ),

                "actual_services": (
                    ", ".join(
                        actual_services
                    )
                ),

                "correct": correct,

                "error": error
            }
        )

    # =====================================================
    # Overall result
    # =====================================================

    accuracy = (
        correct_count
        / total
        * 100
    )

    print(
        "\n\n"
        "========================================"
    )

    print(
        "OVERALL RESULT"
    )

    print(
        "========================================"
    )

    print(
        f"Correct: "
        f"{correct_count}/{total}"
    )

    print(
        f"Accuracy: "
        f"{accuracy:.1f}%"
    )

    # =====================================================
    # Category result
    # =====================================================

    print(
        "\n"
        "CATEGORY RESULTS"
    )

    print(
        "----------------------------------------"
    )

    for category, stats in (
        category_stats.items()
    ):

        category_accuracy = (
            stats["correct"]
            / stats["total"]
            * 100
        )

        print(
            f"{category:<15} "
            f"{stats['correct']}/"
            f"{stats['total']} "
            f"({category_accuracy:.1f}%)"
        )

    # =====================================================
    # Save CSV
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
                "correct",
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