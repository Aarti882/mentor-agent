from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, START, END

# Import the specialized agents/modules
from agents.market_research import get_market_requirements
from agents.evaluator import evaluate_resume
from agents.learning_path import generate_learning_path
from models.predictive_engine import get_predictive_engine
import database as db

# 1. Define State Schema
class MentorAgentState(TypedDict):
    # Inputs
    user_name: str
    user_email: str
    target_role: str
    timeline_months: int
    resume_text: str
    company_type: str
    placement_route: str
    project_count: int
    api_key: str
    
    # Intermediary outputs
    market_research: Dict[str, Any]
    evaluation: Dict[str, Any]
    predictive_score: float
    learning_path: Dict[str, Any]
    
    # Persistence outputs
    user_id: int

# 2. Define Node Logic
def market_research_node(state: MentorAgentState) -> Dict[str, Any]:
    """Retrieves market expectations for the target role."""
    print("[Supervisor] Routing task to Market Research Agent...")
    target_role = state.get("target_role", "Software Engineer")
    api_key = state.get("api_key", None)
    
    research_results = get_market_requirements(target_role, api_key=api_key)
    return {"market_research": research_results}

def profile_evaluation_node(state: MentorAgentState) -> Dict[str, Any]:
    """Evaluates user resume text against research metrics using ChromaDB."""
    print("[Supervisor] Routing task to Profile Evaluator Agent...")
    resume_text = state.get("resume_text", "")
    market_research = state.get("market_research", {})
    api_key = state.get("api_key", None)
    
    evaluation_results = evaluate_resume(resume_text, market_research, api_key=api_key)
    return {"evaluation": evaluation_results}

def predictive_analysis_node(state: MentorAgentState) -> Dict[str, Any]:
    """Runs target stats through traditional ML model for success probability."""
    print("[Supervisor] Routing task to Predictive Analytics ML Engine...")
    evaluation = state.get("evaluation", {})
    project_count = state.get("project_count", 0)
    company_type = state.get("company_type", "Service-based")
    placement_route = state.get("placement_route", "On-campus")
    
    skill_match = evaluation.get("skill_match_score", 0.0)
    resume_opt = evaluation.get("resume_opt_score", 0.0)
    
    # Get singleton engine
    ml_engine = get_predictive_engine()
    score = ml_engine.predict_callback(
        skill_match=skill_match,
        resume_opt=resume_opt,
        projects=project_count,
        company_type=company_type,
        placement_route=placement_route
    )
    
    return {"predictive_score": score}

def learning_path_node(state: MentorAgentState) -> Dict[str, Any]:
    """Creates a weekly study program to fill the skill gaps."""
    print("[Supervisor] Routing task to Learning Path & Portfolio Agent...")
    target_role = state.get("target_role", "Software Engineer")
    timeline_months = state.get("timeline_months", 2)
    evaluation = state.get("evaluation", {})
    api_key = state.get("api_key", None)
    
    missing_skills = evaluation.get("missing_skills", [])
    
    path_results = generate_learning_path(
        target_role=target_role,
        timeline_months=timeline_months,
        missing_skills=missing_skills,
        api_key=api_key
    )
    
    return {"learning_path": path_results}

def database_persistence_node(state: MentorAgentState) -> Dict[str, Any]:
    """Saves final state to SQLite database deterministically."""
    print("[Supervisor] Routing final state to SQLite Database...")
    user_name = state.get("user_name", "Anonymous")
    user_email = state.get("user_email", "anonymous@mca.edu")
    target_role = state.get("target_role", "Software Engineer")
    timeline_months = state.get("timeline_months", 2)
    resume_text = state.get("resume_text", "")
    
    evaluation = state.get("evaluation", {})
    project_count = state.get("project_count", 0)
    company_type = state.get("company_type", "Service-based")
    predictive_score = state.get("predictive_score", 0.0)
    learning_path = state.get("learning_path", {})
    
    # Save User Info
    user_id = db.save_user(
        name=user_name,
        email=user_email,
        target_role=target_role,
        timeline_months=timeline_months,
        resume_text=resume_text
    )
    
    # Save Learning Path Milestones
    milestones = learning_path.get("milestones", [])
    db.save_learning_path(user_id=user_id, milestones=milestones)
    
    # Save Prediction History
    db.save_prediction(
        user_id=user_id,
        skill_match_score=evaluation.get("skill_match_score", 0.0),
        resume_opt_score=evaluation.get("resume_opt_score", 0.0),
        project_count=project_count,
        company_type=company_type,
        callback_probability=predictive_score
    )
    
    return {"user_id": user_id}

# 3. Assemble LangGraph Workflow
workflow = StateGraph(MentorAgentState)

# Add Nodes
workflow.add_node("research", market_research_node)
workflow.add_node("evaluate", profile_evaluation_node)
workflow.add_node("predict", predictive_analysis_node)
workflow.add_node("learning_path", learning_path_node)
workflow.add_node("save", database_persistence_node)

# Set Edges
workflow.add_edge(START, "research")
workflow.add_edge("research", "evaluate")
workflow.add_edge("evaluate", "predict")
workflow.add_edge("predict", "learning_path")
workflow.add_edge("learning_path", "save")
workflow.add_edge("save", END)

# Compile
compiled_graph = workflow.compile()

def run_mentor_pipeline(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the MCA Mentor multi-agent workflow from start to end.
    
    inputs: dict with keys matching MentorAgentState keys (e.g. user_name, target_role, etc.)
    """
    initial_state = MentorAgentState(
        user_name=inputs.get("user_name", "Anonymous"),
        user_email=inputs.get("user_email", ""),
        target_role=inputs.get("target_role", "Data Analyst"),
        timeline_months=inputs.get("timeline_months", 2),
        resume_text=inputs.get("resume_text", ""),
        company_type=inputs.get("company_type", "Service-based"),
        placement_route=inputs.get("placement_route", "On-campus"),
        project_count=inputs.get("project_count", 0),
        api_key=inputs.get("api_key", ""),
        market_research={},
        evaluation={},
        predictive_score=0.0,
        learning_path={},
        user_id=-1
    )
    
    # Execute graph synchronously
    result = compiled_graph.invoke(initial_state)
    return result
