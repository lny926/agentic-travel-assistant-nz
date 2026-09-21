import logging

from uuid import uuid4

from langchain_core.messages import (
    HumanMessage
)

from src.graph.workflow import (
    build_graph
)


logging.basicConfig(
    level=logging.ERROR
)


def main():
    graph = build_graph()

    session_id = str(
        uuid4()
    )

    print(
        "Travel AI Assistant"
    )

    print(
        "Type 'exit' or 'quit' to stop."
    )

    print(
        "Type 'new' to start a new conversation."
    )

    while True:
        question = input(
            "\nYou: "
        ).strip()

        if not question:
            continue

        if question.lower() in [
            "exit",
            "quit"
        ]:
            print(
                "\nGoodbye!"
            )
            break

        if question.lower() == "new":
            session_id = str(
                uuid4()
            )

            print(
                "\nStarted a new conversation."
            )

            continue

        try:
            result = graph.invoke(
                {
                    "question": question,

                    "messages": [
                        HumanMessage(
                            content=question
                        )
                    ]
                },

                config={
                    "configurable": {
                        "thread_id": (
                            session_id
                        )
                    }
                }
            )

            services = result.get(
                "services",
                []
            )

            if services:
                print(
                    "\nServices:",
                    ", ".join(
                        services
                    )
                )

            answer = result.get(
                "answer",
                ""
            )

            print(
                "\nAssistant:"
            )

            print(
                answer
                if answer
                else (
                    "Sorry, I couldn't "
                    "generate a response."
                )
            )

            sources = result.get(
                "sources",
                []
            )

            if sources:
                print(
                    "\nSources:",
                    ", ".join(
                        sources
                    )
                )

        except KeyboardInterrupt:
            print(
                "\n\nGoodbye!"
            )
            break

        except Exception as error:
            print(
                "\nSorry, something went wrong."
            )

            print(
                f"Error: {error}"
            )


if __name__ == "__main__":
    main()