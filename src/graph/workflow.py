from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.checkpoint.memory import (
    InMemorySaver
)

from src.graph.state import TravelState
from src.graph.planner import planner_node

from src.graph.nodes import (
    execute_services_node,
    final_synthesizer_node
)


def build_graph():
    builder = StateGraph(
        TravelState
    )

    # Nodes
    builder.add_node(
        "planner",
        planner_node
    )

    builder.add_node(
        "executor",
        execute_services_node
    )

    builder.add_node(
        "synthesizer",
        final_synthesizer_node
    )

    # Workflow
    builder.add_edge(
        START,
        "planner"
    )

    builder.add_edge(
        "planner",
        "executor"
    )

    builder.add_edge(
        "executor",
        "synthesizer"
    )

    builder.add_edge(
        "synthesizer",
        END
    )

    # Conversation memory
    memory = InMemorySaver()

    return builder.compile(
        checkpointer=memory
    )