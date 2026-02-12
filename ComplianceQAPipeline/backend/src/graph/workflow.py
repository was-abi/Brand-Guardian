'''
This module defines the DAG:  Directed Acyclic graph
It connects nodes using stategraph from langgraph
START -> index_video_node -> audit_content_node -> END
'''

from langgraph.graph import StateGraph, END
from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import (
    index_video_node, 
    audio_content_node
    )

def create_graph():
    '''
        Constructs and compiles the langgraph workflow
        Returns a compiled graph: runnable graph object for execution
    '''
    #Initialize the graph with state schema
    workflow = StateGraph(initial_state=VideoAuditState)
    #add the nodes
    workflow.add_node("indexer", index_video_node)
    workflow.add_node("auditor", audio_content_node)
 
    #define the entry point: indexer
    workflow.set_entry_point("indexer")
    #define the edges
    workflow.add_edge("indexer", "auditor")
    workflow.add_edge("auditor", END)
    #compile the graph
    app = workflow.compile()
    return app

#expose this runnable app
app = create_graph()
