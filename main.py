import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional

# Import agents and database layers
import database as db
from agents.supervisor import run_mentor_pipeline
from utils.helpers import extract_text_from_pdf, clean_text

app = FastAPI(title="MCA Mentor Agent API Gateway", version="1.0.0")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- PYDANTIC REQUEST SCHEMAS -----------------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class DirectLoginRequest(BaseModel):
    email: EmailStr
    name: str

class MilestoneToggleRequest(BaseModel):
    week_number: int
    completed: bool

# ----------------- AUTH ENDPOINTS -----------------
@app.get("/api/users")
def get_users():
    try:
        users = db.get_all_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {e}")

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    try:
        user_id = db.register_user(req.name, req.email, req.password)
        return {
            "user_id": user_id,
            "name": req.name,
            "email": req.email,
            "message": "User registered successfully."
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {e}")

@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = db.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials. Verify your email or password."
        )
    return {
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "target_role": user["target_role"],
        "timeline_months": user["timeline_months"],
        "message": "Login successful."
    }

@app.post("/api/auth/direct")
def direct_login(req: DirectLoginRequest):
    try:
        # Check if user exists by email
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, target_role, timeline_months FROM users WHERE email = ?", (req.email.strip().lower(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user = dict(row)
            return {
                "user_id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "target_role": user["target_role"],
                "timeline_months": user["timeline_months"],
                "message": "Direct login successful."
            }
        else:
            # User doesn't exist, register them dynamically with google fallback secret password
            user_id = db.register_user(req.name, req.email, "google_oauth_fallback_secret_password_phrase")
            return {
                "user_id": user_id,
                "name": req.name,
                "email": req.email,
                "target_role": None,
                "timeline_months": None,
                "message": "Direct login registered and logged in successfully."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Direct authentication failed: {e}")


# ----------------- CAREER DIAGNOSTICS PIPELINE -----------------
@app.post("/api/diagnose")
async def run_diagnose(
    user_id: int = Form(...),
    target_role: str = Form(...),
    timeline_months: int = Form(...),
    company_type: str = Form(...),
    placement_route: str = Form(...),
    project_count: int = Form(...),
    api_key: Optional[str] = Form(""),
    resume: UploadFile = File(...)
):
    # Retrieve user data from DB to get their details (name, email)
    user_data = db.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User account not found.")

    # Read and parse uploaded resume file
    try:
        content_type = resume.content_type
        file_bytes = await resume.read()
        
        if content_type == "application/pdf" or resume.filename.endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_bytes)
        else:
            resume_text = clean_text(file_bytes.decode("utf-8", errors="ignore"))
            
        if not resume_text:
            raise ValueError("Resume file is empty or text extraction failed.")
            
    except Exception as parse_error:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to parse uploaded resume: {parse_error}"
        )

    # Prepare inputs for LangGraph pipeline
    inputs = {
        "user_name": user_data["name"],
        "user_email": user_data["email"],
        "target_role": target_role,
        "timeline_months": timeline_months,
        "resume_text": resume_text,
        "company_type": company_type,
        "placement_route": placement_route,
        "project_count": project_count,
        "api_key": api_key
    }

    try:
        # Run LangGraph Orchestrator pipeline
        pipeline_output = run_mentor_pipeline(inputs)
        
        # Serialize and save generated learning_path/roadmap JSON directly inside users table
        roadmap_data = pipeline_output.get("learning_path", {})
        roadmap_json = json.dumps(roadmap_data)
        
        db.update_user_profile(
            user_id=user_id,
            target_role=target_role,
            timeline_months=timeline_months,
            resume_text=resume_text,
            roadmap_json=roadmap_json
        )
        
        # Format and return JSON payload
        return {
            "user_id": user_id,
            "market_research": pipeline_output.get("market_research", {}),
            "evaluation": pipeline_output.get("evaluation", {}),
            "predictive_score": pipeline_output.get("predictive_score", 0.0),
            "learning_path": roadmap_data
        }
        
    except Exception as pipeline_error:
        raise HTTPException(
            status_code=500, 
            detail=f"LangGraph execution pipeline failed: {pipeline_error}"
        )

# ----------------- ROADMAP AND PORTFOLIO BLUEPRINTS -----------------
@app.get("/api/users/{user_id}/roadmap")
def get_roadmap(user_id: int):
    user_data = db.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Retrieve base serialized roadmap details
    roadmap_json = user_data.get("roadmap_json")
    if not roadmap_json:
        return {
            "milestones": [],
            "projects": [],
            "learning_resources": [],
            "message": "No roadmap generated yet. Complete diagnostics."
        }
        
    roadmap_data = json.loads(roadmap_json)
    
    # Retrieve current checkbox states from SQLite to ensure sync
    completed_milestones = db.get_learning_path(user_id)
    completed_map = {m["week_number"]: bool(m["completed"]) for m in completed_milestones}
    
    # Merge completion status back into milestones
    if "milestones" in roadmap_data:
        for milestone in roadmap_data["milestones"]:
            week = milestone.get("week_number")
            milestone["completed"] = completed_map.get(week, False)
            
    return roadmap_data

@app.put("/api/users/{user_id}/roadmap/milestone")
def toggle_milestone(user_id: int, req: MilestoneToggleRequest):
    user_data = db.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found.")
        
    try:
        db.update_milestone_status(user_id, req.week_number, req.completed)
        return {"message": f"Week {req.week_number} status updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- HISTORICAL ANALYTICS -----------------
@app.get("/api/users/{user_id}/history")
def get_history(user_id: int):
    user_data = db.get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found.")
        
    history = db.get_predictions_history(user_id)
    return {"history": history}

if __name__ == "__main__":
    import uvicorn
    # Start web api server
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
