from langgraph.graph import StateGraph,START,END 
from langgraph.prebuilt import ToolNode,tools_condition
from src.core.tools import verify_prescription
from src.core.agents.prescription_agent import AgentHub, PrescriptionAgent

hub = AgentHub()
tools = [verify_prescription]
tool_node = ToolNode(tools)
graph = StateGraph(PrescriptionAgent)
graph.add_node("sub_agent",hub.sub_agent)
graph.add_node("coordinator",hub.coordinator_agent)
graph.add_node("tools",tool_node)

graph.add_edge(START,"sub_agent")
graph.add_edge("sub_agent", "coordinator")
graph.add_conditional_edges("coordinator", tools_condition)
graph.add_edge("tools", "coordinator")
graph.add_edge("coordinator", END)

graph_builder = graph.compile()

