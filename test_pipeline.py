import sys
import os

# Ensure the current directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database as db
from models.predictive_engine import get_predictive_engine
from agents.evaluator import evaluate_resume
from agents.market_research import get_market_requirements
from agents.learning_path import generate_learning_path
from agents.supervisor import run_mentor_pipeline

def test_database():
    print("Testing Database initialization and saving user...")
    db.init_db()
    
    # Save a user
    user_id = db.save_user(
        name="Test Candidate",
        email="test@mca.edu",
        target_role="ML Engineer",
        timeline_months=3,
        resume_text="Experienced Python developer with machine learning experience."
    )
    assert user_id is not None, "Failed to save user"
    print(f"User saved successfully with ID: {user_id}")
    
    # Save a dummy milestone
    milestones = [{"week_number": 1, "topic": "Python Basics", "deliverable": "Write a script"}]
    db.save_learning_path(user_id, milestones)
    
    # Retrieve it
    path = db.get_learning_path(user_id)
    assert len(path) == 1, "Failed to retrieve learning path"
    print("Learning path saved and retrieved successfully.")
    
    # Check completion update
    db.update_milestone_status(user_id, 1, True)
    path_updated = db.get_learning_path(user_id)
    assert path_updated[0]['completed'] == 1, "Failed to update milestone completion"
    print("Milestone completion updated successfully.")
    
    # Save a dummy prediction
    db.save_prediction(user_id, 0.8, 0.7, 3, "Product-based", 65.5)
    history = db.get_predictions_history(user_id)
    assert len(history) >= 1, "Failed to retrieve predictions history"
    print("Prediction saved and history retrieved successfully.")
    print("Database Tests Passed!\n")

def test_predictive_engine():
    print("Testing Predictive Analytics ML Engine...")
    engine = get_predictive_engine()
    assert engine.model is not None, "ML Model was not loaded/trained"
    
    # Predict callback
    prob = engine.predict_callback(
        skill_match=0.8,
        resume_opt=0.9,
        projects=3,
        company_type="Product-based",
        placement_route="Off-campus"
    )
    print(f"Predicted success probability: {prob}%")
    assert 0.0 <= prob <= 100.0, "Probability out of range"
    print("Predictive Engine Tests Passed!\n")

def test_evaluator_and_chroma():
    print("Testing Profile Evaluator & ChromaDB vector index...")
    sample_resume = """
    Demo Student
    Email: student.demo@gmail.com | Phone: +91-0000000000
    
    Education:
    Master of Computer Applications (MCA), 2026
    
    Skills:
    Python, SQL, Pandas, Git, Jupyter Notebook, TensorFlow
    
    Projects:
    1. E-commerce dashboard using Streamlit, Python and Postgres.
    """
    
    target_reqs = {
        "hard_skills": ["Python", "SQL", "Pandas", "PyTorch", "Docker"],
        "tools": ["Git", "Jupyter Notebook", "PostgreSQL", "ChromaDB"]
    }
    
    results = evaluate_resume(sample_resume, target_reqs, api_key=None)
    print("Evaluator results:", results)
    
    assert results['skill_match_score'] > 0.0, "Skill match score should be greater than zero"
    assert results['resume_opt_score'] > 0.0, "Resume optimization score should be greater than zero"
    assert "Python" in results['matched_skills'], "Python should be matched"
    assert "Docker" in results['missing_skills'], "Docker should be missing"
    print("Evaluator & ChromaDB Tests Passed!\n")

def test_market_research_and_learning_path():
    print("Testing Market Research & Learning Path Local Fallbacks...")
    market_reqs = get_market_requirements("Agentic AI Developer", api_key=None)
    print("Market requirements:", market_reqs)
    assert market_reqs['role'] == "Agentic AI Developer", "Market research role mismatch"
    
    curriculum = generate_learning_path("Agentic AI Developer", 2, ["LangGraph", "ChromaDB"], api_key=None)
    print("Curriculum milestones count:", len(curriculum['milestones']))
    assert len(curriculum['milestones']) == 8, "Expected 8 weeks of milestone deliverables for 2 months"
    print("Market Research & Learning Path Tests Passed!\n")

def test_supervisor_pipeline():
    print("Testing complete Supervisor multi-agent LangGraph workflow...")
    sample_resume = """
    Demo Student
    MCA student. Skills: Python, Pandas, SQLite, Power BI, Git. Completed 2 projects.
    """
    
    inputs = {
        "user_name": "Demo Student",
        "user_email": "student@mca.edu",
        "target_role": "Data Analyst",
        "timeline_months": 1,
        "resume_text": sample_resume,
        "company_type": "Service-based",
        "placement_route": "On-campus",
        "project_count": 2,
        "api_key": "" # No API Key for test run
    }
    
    outputs = run_mentor_pipeline(inputs)
    print("Supervisor execution outputs keys:", outputs.keys())
    assert outputs['user_id'] != -1, "Pipeline did not save state to database"
    assert outputs['predictive_score'] > 0.0, "Pipeline did not compute predictive score"
    assert len(outputs['learning_path']['milestones']) == 4, "Expected 4 weeks of syllabus for 1 month"
    print(f"Pipeline executed successfully. Saved User ID: {outputs['user_id']}, Callback Success Rate: {outputs['predictive_score']}%")
    print("Supervisor LangGraph Pipeline Tests Passed!\n")

if __name__ == "__main__":
    print("=== STARTING MCA MENTOR PIPELINE INTEGRATION TESTS ===\n")
    try:
        test_database()
        test_predictive_engine()
        test_evaluator_and_chroma()
        test_market_research_and_learning_path()
        test_supervisor_pipeline()
        print("=== ALL MENTOR AGENT INTEGRATION TESTS PASSED SUCCESSFULLY! ===")
    except AssertionError as ae:
        print(f"\n[ERROR] Assertion Failed: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
