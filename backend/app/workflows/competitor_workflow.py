from langgraph.graph import END, START, StateGraph

from app.agents.state import CompetitorAgentState
from app.workflows.nodes import (
    scoring_node,
    uploaded_evidence_node,
    research_evidence_node,
    research_node,
    battlecard_node,
    route_after_scoring,
    finish_node,
)


def build_competitor_workflow():
    graph = StateGraph(CompetitorAgentState)

    graph.add_node("scoring", scoring_node)
    graph.add_node("uploaded_evidence", uploaded_evidence_node)
    graph.add_node("research", research_node)
    graph.add_node("research_evidence", research_evidence_node)
    graph.add_node("battlecard", battlecard_node)
    graph.add_node("finish", finish_node)

    graph.add_edge(START, "scoring")
    graph.add_edge("scoring", "uploaded_evidence")

    graph.add_conditional_edges(
        "uploaded_evidence",
        route_after_scoring,
        {
            "research": "research",
            "finish": "finish",
        },
    )

    graph.add_edge("research", "research_evidence")
    graph.add_edge("research_evidence", "battlecard")
    graph.add_edge("battlecard", "finish")
    graph.add_edge("finish", END)

    return graph.compile()