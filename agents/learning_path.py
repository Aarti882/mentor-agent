import json
from pydantic import BaseModel, Field
from typing import List
from utils.helpers import call_gemini

class StudyWeek(BaseModel):
    week_number: int = Field(description="The week number, starting from 1")
    topic: str = Field(description="The core skill, concept, or technology to learn this week")
    deliverable: str = Field(description="A concrete, measurable task or small coding build the user must complete this week")

class PortfolioProject(BaseModel):
    name: str = Field(description="A catchy name for the portfolio project")
    description: str = Field(description="A detailed description of the project and why it helps showcase the missing skills to recruiters")
    tech_stack: List[str] = Field(description="List of technologies, databases, and frameworks used in this project")
    steps: List[str] = Field(description="Step-by-step implementation guide for building this project")

class ResourceLink(BaseModel):
    topic: str = Field(description="The skill or tool this resource covers")
    resource_name: str = Field(description="Name of the platform or search query (e.g. 'FreeCodeCamp SQL Roadmap')")
    suggested_search: str = Field(description="A detailed YouTube/Google search query for high quality free learning")

class LearningPathResponse(BaseModel):
    milestones: List[StudyWeek] = Field(description="A week-by-week structured curriculum covering the timeline")
    projects: List[PortfolioProject] = Field(description="1 or 2 tailored portfolio project suggestions")
    learning_resources: List[ResourceLink] = Field(description="Key recommended free learning resources")

def _generate_programmatic_fallback(target_role: str, timeline_months: int, missing_skills: List[str]) -> dict:
    """Programmatic fallback curriculum generator if LLM is unavailable."""
    total_weeks = timeline_months * 4
    
    # Ensure we have skills to learn
    skills_to_learn = missing_skills.copy()
    if not skills_to_learn:
        # If no skills are missing, suggest advanced topics for the role
        if "Agentic" in target_role or "AI" in target_role:
            skills_to_learn = ["LangGraph workflows", "Advanced RAG optimization", "Multi-Agent systems", "LLM Evaluation frameworks"]
        elif "ML" in target_role or "Machine" in target_role:
            skills_to_learn = ["Hyperparameter Tuning", "MLOps & Docker", "FastAPI deployment", "Deep learning architectures"]
        else:
            skills_to_learn = ["Advanced SQL joins", "Data warehousing", "Streamlit dashboarding", "Statistical hypothesis testing"]

    milestones = []
    # Distribute skills across available weeks
    for w in range(1, total_weeks + 1):
        # Pick a skill based on round robin
        skill_idx = (w - 1) % len(skills_to_learn)
        skill = skills_to_learn[skill_idx]
        
        milestones.append({
            "week_number": w,
            "topic": f"Mastering {skill}",
            "deliverable": f"Implement a mini project or write code showcasing {skill} in Python."
        })
        
    # Generate role-specific portfolio projects
    projects = []
    if "Agentic" in target_role or "AI" in target_role:
        projects.append({
            "name": "Autonomous Customer Support Agent Suite",
            "description": "An end-to-end multi-agent ticketing system that reads incoming queries, searches a knowledge base (ChromaDB), routes specialized tasks (refunds, bugs, inquiries) to subagents, and generates draft replies.",
            "tech_stack": ["Python", "LangGraph", "ChromaDB", "Streamlit", "Gemini API"],
            "steps": [
                "Setup ChromaDB and insert mock documentation.",
                "Build custom routing logic with LangGraph state graphs.",
                "Implement tool calling for DB queries.",
                "Build a Streamlit interface for user testing."
            ]
        })
    elif "ML" in target_role or "Machine" in target_role:
        projects.append({
            "name": "End-to-End MLOps Predictive Pipeline",
            "description": "A production-grade ML pipeline that trains a model on historical data, serializes the artifacts, and serves predictions via a FastAPI backend hosted inside a Docker container.",
            "tech_stack": ["Python", "Scikit-Learn", "FastAPI", "Docker", "Git"],
            "steps": [
                "Train classifier and save joblib object.",
                "Develop FastAPI endpoints for /predict and /train.",
                "Write a Dockerfile and containerize the environment.",
                "Test API response latency and reliability."
            ]
        })
    else:
        projects.append({
            "name": "E-Commerce Customer Insights Dashboard",
            "description": "A relational database analytical system that queries transactional logs using SQL, calculates customer lifetime value (CLV), and renders interactive dashboards for marketing teams.",
            "tech_stack": ["Python", "SQL / PostgreSQL", "Pandas", "Streamlit", "Plotly"],
            "steps": [
                "Design normalized schema and insert mock orders data.",
                "Write SQL queries to find top buying segments.",
                "Build interactive filters and charts in Streamlit.",
                "Calculate CLV and write cohort retention reports."
            ]
        })

    # Generate helpful resource links
    learning_resources = []
    for skill in skills_to_learn[:3]:
        learning_resources.append({
            "topic": skill,
            "resource_name": f"YouTube {skill} Practical Tutorial",
            "suggested_search": f"{skill} tutorial for beginners step by step"
        })
        
    return {
        "milestones": milestones,
        "projects": projects,
        "learning_resources": learning_resources
    }

def generate_learning_path(target_role: str, timeline_months: int, missing_skills: List[str], api_key: str = None) -> dict:
    """Generates a week-by-week learning path and portfolio project recommendations."""
    if api_key:
        prompt = f"""
        Act as a professional technical mentor and curriculum architect for Indian MCA students.
        Create a personalized learning plan targeting the role '{target_role}' over a period of {timeline_months} months ({timeline_months * 4} weeks).
        The student has the following missing skills/tools that need to be prioritized: {', '.join(missing_skills) if missing_skills else 'None identified (give advanced study)'}.
        
        Requirements:
        1. Create exactly {timeline_months * 4} weekly modules.
        2. Outline weekly topics and highly practical, measurable deliverables.
        3. Suggest 1 or 2 highly engaging portfolio projects that target the missing skills and look premium on a resume.
        4. Suggest specific YouTube/Google search queries to locate high quality free tutorials.
        """
        try:
            response_text = call_gemini(
                prompt=prompt,
                api_key=api_key,
                system_instruction="You are a Career & Study Plan Mentor. Output your curriculum details strictly in JSON format matching the schema.",
                response_schema=LearningPathResponse
            )
            return json.loads(response_text)
        except Exception as e:
            print(f"Learning Path Agent LLM call failed, returning fallback: {e}")

    # Return fallback
    return _generate_programmatic_fallback(target_role, timeline_months, missing_skills)
