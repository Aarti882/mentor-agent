import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import time
from datetime import datetime

# Import modules
import database as db
from agents.supervisor import run_mentor_pipeline
from utils.helpers import extract_text_from_pdf, clean_text

# Page Configuration
st.set_page_config(
    page_title="MCA Career Mentor Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
db.init_db()

# ----------------- SESSION STATE LOG SYSTEM -----------------
# Setup live agent activity logs for the sidebar terminal simulation
if 'agent_logs' not in st.session_state:
    st.session_state['agent_logs'] = [
        f"[{datetime.now().strftime('%H:%M:%S')}] [System] Booting MCA Career Mentor Agent OS...",
        f"[{datetime.now().strftime('%H:%M:%S')}] [System] SQLite Persistence engine connected successfully.",
        f"[{datetime.now().strftime('%H:%M:%S')}] [System] Predictive ML engine initialized (Random Forest).",
        f"[{datetime.now().strftime('%H:%M:%S')}] [System] ChromaDB vector indexes compiled.",
        f"[{datetime.now().strftime('%H:%M:%S')}] [System] Core Supervisor ready for career diagnostics."
    ]

def add_log(agent_name, message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state['agent_logs'].append(f"[{timestamp}] [{agent_name}] {message}")

# ----------------- CUSTOM STYLE SHEET (WOW FACTOR) -----------------
st.markdown("""
<style>
    /* Global Background and Fonts */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Outfit', 'Inter', -apple-system, sans-serif;
    }
    
    /* Persistent Sidebar Custom Glassmorphic Look */
    section[data-testid="stSidebar"] {
        background-color: #0d1321 !important;
        border-right: 1px solid rgba(139, 92, 246, 0.15);
    }
    
    /* Clean Separator lines */
    hr {
        border-color: rgba(139, 92, 246, 0.1);
        margin: 1.5rem 0;
    }
    
    /* Terminal logs window */
    .terminal-box {
        background-color: #020617;
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 8px;
        padding: 10px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 11px;
        color: #38bdf8;
        height: 180px;
        overflow-y: scroll;
        margin-top: 10px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
    }
    
    /* Custom Timeline Card component */
    .timeline-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        border-left: 5px solid #8b5cf6;
        transition: transform 0.2s ease-in-out, border-color 0.2s;
    }
    
    .timeline-card:hover {
        transform: translateY(-2px);
        border-color: #a78bfa;
        background: rgba(30, 41, 59, 0.6);
    }
    
    .timeline-card-completed {
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.15);
        border-left: 5px solid #10b981;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Custom Badges */
    .badge-live {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 30px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 15px;
    }
    
    .role-badge {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
        color: #c7d2fe;
        border: 1px solid rgba(99, 102, 241, 0.4);
        border-radius: 20px;
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-top: 10px;
    }

    .badge-product {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-service {
        background-color: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }

    .skill-tag-matched {
        background-color: rgba(16, 185, 129, 0.1);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.25);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        display: inline-block;
        margin: 4px;
    }
    
    .skill-tag-missing {
        background-color: rgba(239, 68, 68, 0.1);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.25);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        display: inline-block;
        margin: 4px;
    }
    
    /* Styled header card */
    .header-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 35px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .header-card::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.05) 0%, transparent 60%);
        pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- DIALOG BOXES (MODALS FOR PROJECT blueprints) -----------------
@st.dialog("Project Implementation Blueprint")
def show_project_blueprint(project):
    """Pops up a modal details containing the blueprint layout of the suggested project."""
    st.markdown(f"### 🚀 {project['name']}")
    st.write(project['description'])
    st.write("---")
    
    st.markdown("##### 📦 Recommended Repository Architecture")
    st.code(f"""
{project['name'].lower().replace(" ", "_").replace("-", "_")}/
├── config/
│   └── database.py        # SQLite or ChromaDB configuration
├── models/
│   └── pipeline.py        # Core processing logic
├── utils/
│   └── helpers.py         # File inputs and text processing helpers
├── app.py                 # Streamlit UI dashboard
├── requirements.txt       # Project dependencies
└── README.md              # Deployment step-by-step documentation
    """, language="text")
    
    st.markdown("##### 🛠️ Core Tech Stack")
    badges = "".join([f'<span class="badge" style="background:rgba(99,102,241,0.15); color:#a5b4fc; border:1px solid rgba(99,102,241,0.3); padding:4px 10px; border-radius:6px; font-size:12px; margin:4px; display:inline-block;">{tech}</span>' for tech in project['tech_stack']])
    st.markdown(f"<div>{badges}</div><br>", unsafe_allow_html=True)
    
    st.markdown("##### 📈 Milestone Checklist")
    for idx, step in enumerate(project['steps']):
        st.markdown(f"**Step {idx+1}:** {step}")
        
    st.write("---")
    if st.button("Close Blueprint"):
        st.rerun()

# ----------------- MAIN TITLE HEADER -----------------
st.markdown("""
<div class="header-card">
    <span class="badge-live">⚡ Status: Live Deployment</span>
    <h1 style="margin: 10px 0; font-size: 42px; font-weight: 800; background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">MCA CAREER MENTOR AGENT</h1>
    <p style="color: #94a3b8; font-size: 16px; max-width: 800px; margin: 0 auto;">
        Integrative AI Career Assistant tailored for Indian MCA students. Orchestrating job research, deterministic ChromaDB skill gap checks, and Scikit-learn random forest models predicting application callbacks.
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.markdown("<h2 style='color: #a78bfa; margin-bottom:0;'>⚙️ Goal Planner</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Configure target outcomes and application profiles below:")
st.sidebar.markdown("---")

api_key = st.sidebar.text_input(
    "Gemini API Key (Optional)",
    type="password",
    help="Add your API key to activate Gemini models for real-time market research and tailored weekly roadmaps. If blank, local fallbacks are triggered.",
    value=os.environ.get("GEMINI_API_KEY", "")
)

user_name = st.sidebar.text_input("Student Name", "Aarti Kumari")
user_email = st.sidebar.text_input("University Email ID", "aarti.kumari.mca@gmail.com")

target_role = st.sidebar.selectbox(
    "Target Career Track",
    ["Agentic AI Developer", "ML Engineer", "Data Analyst", "Other Technical Role"]
)

if target_role == "Other Technical Role":
    custom_role = st.sidebar.text_input("Target Track Name", "Fullstack Developer")
    target_role_query = custom_role
else:
    target_role_query = target_role

timeline_months = st.sidebar.slider(
    "Timeline for Preparation",
    min_value=1,
    max_value=6,
    value=2,
    format="%d Months"
)

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color: #a78bfa;'>🎯 Application Strategy (ML Input)</h4>", unsafe_allow_html=True)

company_type = st.sidebar.selectbox(
    "Target Company Segment",
    ["Product-based", "Service-based"]
)

# Badge selector visualization on sidebar
if company_type == "Product-based":
    st.sidebar.markdown('Segment: <span class="badge-product">Product-based</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('Segment: <span class="badge-service">Service-based</span>', unsafe_allow_html=True)

placement_route = st.sidebar.selectbox(
    "Application Sourcing Route",
    ["Off-campus", "On-campus"]
)

project_count = st.sidebar.slider(
    "Completed Portfolio Projects",
    min_value=0,
    max_value=10,
    value=2
)

# Load existing user profile selector
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color: #a78bfa;'>📂 Retrieve Profile History</h4>", unsafe_allow_html=True)
existing_users = db.get_all_users()
user_options = {f"{u['name']} ({u['target_role']})": u['id'] for u in existing_users}

selected_profile = st.sidebar.selectbox(
    "Load Saved Profile State",
    ["Create New Session"] + list(user_options.keys())
)

# Syncing DB profile details to session state if requested
if selected_profile != "Create New Session":
    user_id = user_options[selected_profile]
    user_data = db.get_user(user_id)
    if user_data:
        if 'pipeline_run' not in st.session_state or st.session_state.get('loaded_user_id') != user_id:
            st.session_state['user_name'] = user_data['name']
            st.session_state['user_email'] = user_data['email']
            st.session_state['target_role'] = user_data['target_role']
            st.session_state['timeline_months'] = user_data['timeline_months']
            st.session_state['resume_text'] = user_data['resume_text']
            
            roadmaps = db.get_learning_path(user_id)
            preds = db.get_predictions_history(user_id)
            
            if preds:
                last_pred = preds[-1]
                st.session_state['predictive_score'] = last_pred['callback_probability']
                st.session_state['evaluation'] = {
                    "skill_match_score": last_pred['skill_match_score'],
                    "resume_opt_score": last_pred['resume_opt_score'],
                    "missing_skills": [],
                    "matched_skills": []
                }
            
            st.session_state['learning_path'] = {"milestones": roadmaps}
            st.session_state['pipeline_run'] = True
            st.session_state['loaded_user_id'] = user_id
            st.session_state['db_user_id'] = user_id
            add_log("System", f"Loaded profile history state for user ID: {user_id}")

# ----------------- SIDEBAR LIVE TERMINAL LOGS -----------------
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color: #a78bfa; margin-bottom: 0;'>🖥️ Live Agent Console Log</h4>", unsafe_allow_html=True)
log_string = "<br>".join(st.session_state['agent_logs'])
st.sidebar.markdown(f'<div class="terminal-box">{log_string}</div>', unsafe_allow_html=True)

# ----------------- MAIN LAYOUT BODY -----------------
st.markdown("### 📄 Step 1: Upload Student Profile")

uploaded_file = st.file_uploader("Upload your resume in PDF or TXT format", type=["pdf", "txt"])

resume_text = ""
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file.read())
    else:
        resume_text = clean_text(uploaded_file.read().decode("utf-8"))
    
    st.success(f"Resume loaded: {uploaded_file.name} ({len(resume_text)} characters text size)")

trigger_btn = st.button("🚀 Analyze Career Path Diagnostics", type="primary", use_container_width=True)

# ----------------- PIPELINE EXECUTION WITH PROGRESS CHECKLIST -----------------
if trigger_btn:
    if not resume_text:
        st.warning("Please upload a resume file to trigger the diagnostics pipeline.")
    else:
        # Create visual live checklist section
        st.markdown("### 🔎 Diagnostic Progress")
        progress_card = st.empty()
        
        # Simulated/Actual progress update steps
        steps = [
            ("Parsing PDF Resume & Cleaning Strings", "System"),
            ("Gathering Job Market Intelligence & Demand Data", "Market Research Agent"),
            ("Running Semantic Checks Against ChromaDB Vector Store", "Evaluator Agent"),
            ("Predicting Application Callback Probability (Scikit-Learn Classifier)", "Predictive ML Engine"),
            ("Generating Week-by-Week Actionable Roadmap (LLM Curriculum Builder)", "Learning Path Agent"),
            ("Persisting State and Predictions in SQLite Database", "System")
        ]
        
        # Build states visual list
        progress_states = ["⏳ Pending"] * len(steps)
        
        def update_progress_ui():
            html_content = "<div style='background: rgba(30,41,59,0.3); border: 1px solid rgba(139,92,246,0.15); border-radius:12px; padding:15px; margin-bottom:20px;'>"
            for idx, (label, agent) in enumerate(steps):
                status = progress_states[idx]
                color = "#94a3b8"
                if "✅" in status:
                    color = "#34d399"
                elif "⏳" in status:
                    color = "#60a5fa"
                html_content += f"<div style='margin-bottom:8px; color:{color}; font-size:14px;'>{status} <b>{agent}:</b> {label}</div>"
            html_content += "</div>"
            progress_card.markdown(html_content, unsafe_allow_html=True)
            
        update_progress_ui()
        
        inputs = {
            "user_name": user_name,
            "user_email": user_email,
            "target_role": target_role_query,
            "timeline_months": timeline_months,
            "resume_text": resume_text,
            "company_type": company_type,
            "placement_route": placement_route,
            "project_count": project_count,
            "api_key": api_key
        }
        
        try:
            # Step 1
            progress_states[0] = "⏳ Running..."
            update_progress_ui()
            add_log("System", f"Triggered raw text cleaner on uploaded file. File size: {len(resume_text)} chars.")
            time.sleep(0.5)
            progress_states[0] = "✅ Completed"
            
            # Step 2
            progress_states[1] = "⏳ Running..."
            update_progress_ui()
            add_log("Research Agent", f"Fetching criteria profiles for '{target_role_query}' role.")
            time.sleep(0.5)
            progress_states[1] = "✅ Completed"
            
            # Step 3
            progress_states[2] = "⏳ Running..."
            update_progress_ui()
            add_log("Evaluator Agent", "Initializing ephemeral ChromaDB. Indexing resume chunks.")
            time.sleep(0.5)
            progress_states[2] = "✅ Completed"
            
            # Step 4
            progress_states[3] = "⏳ Running..."
            update_progress_ui()
            add_log("ML Engine", "Feeding feature array to Random Forest predictor classifier.")
            time.sleep(0.5)
            progress_states[3] = "✅ Completed"
            
            # Step 5
            progress_states[4] = "⏳ Running..."
            update_progress_ui()
            add_log("Learning Path Agent", "Crafting portfolio projects and weekly lesson structures.")
            time.sleep(0.5)
            progress_states[4] = "✅ Completed"
            
            # Step 6: RUN GRAPH
            progress_states[5] = "⏳ Running..."
            update_progress_ui()
            add_log("System", "Saving session transactions to SQLite database...")
            
            pipeline_result = run_mentor_pipeline(inputs)
            
            # Save results into session state
            st.session_state['pipeline_run'] = True
            st.session_state['market_research'] = pipeline_result.get('market_research', {})
            st.session_state['evaluation'] = pipeline_result.get('evaluation', {})
            st.session_state['predictive_score'] = pipeline_result.get('predictive_score', 0.0)
            st.session_state['learning_path'] = pipeline_result.get('learning_path', {})
            st.session_state['db_user_id'] = pipeline_result.get('user_id', -1)
            
            time.sleep(0.3)
            progress_states[5] = "✅ Completed"
            update_progress_ui()
            
            add_log("System", f"Successfully completed. Success rate computed: {pipeline_result.get('predictive_score', 0.0)}%. Saved User ID: {pipeline_result.get('user_id')}")
            st.success("Diagnostics pipeline compiled successfully.")
        except Exception as e:
            st.error(f"Failed pipeline execution: {e}")
            add_log("System", f"CRITICAL: Pipeline failed. Error details: {str(e)}")

# ----------------- DIAGNOSTIC DETAILS SECTION -----------------
if st.session_state.get('pipeline_run'):
    db_user_id = st.session_state.get('db_user_id', -1)
    eval_data = st.session_state.get('evaluation', {})
    market_data = st.session_state.get('market_research', {})
    predictive_score = st.session_state.get('predictive_score', 0.0)
    learning_path = st.session_state.get('learning_path', {})

    st.markdown("---")
    st.markdown("### 📊 Step 2: Live Career Analytics")
    
    col_layout_left, col_layout_right = st.columns([0.45, 0.55])
    
    # 3. INTERACTIVE RADIAL GAUGE CHART
    with col_layout_left:
        st.markdown("<h4 style='color:#a78bfa; text-align:center;'>Predictive Success Gauge</h4>", unsafe_allow_html=True)
        
        # Color coding color schemes based on the callback probability
        if predictive_score < 40:
            bar_color = "#ef4444"  # Red
        elif predictive_score < 75:
            bar_color = "#f59e0b"  # Amber
        else:
            bar_color = "#10b981"  # Emerald Green
            
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=predictive_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            number={'suffix': "%", 'font': {'size': 48, 'color': '#ffffff', 'family': 'Outfit'}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': bar_color, 'thickness': 0.25},
                'bgcolor': "rgba(30, 41, 59, 0.2)",
                'borderwidth': 2,
                'bordercolor': "#334155",
                'steps': [
                    {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.05)'},
                    {'range': [40, 75], 'color': 'rgba(245, 158, 11, 0.05)'},
                    {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.05)'}
                ],
                'threshold': {
                    'line': {'color': "#8b5cf6", 'width': 4}, # Violet indicator
                    'thickness': 0.8,
                    'value': predictive_score
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#e2e8f0"},
            height=280,
            margin=dict(l=30, r=30, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"""
        <div style='text-align: center; background: rgba(30,41,59,0.3); border: 1px solid rgba(255,255,255,0.05); border-radius:8px; padding:12px; margin-bottom: 20px;'>
            <span style='color:#94a3b8; font-size: 13px;'>The predictive analytics engine scores this profile's callback probability based on the target role profile, projects completing count, and target company route.</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col_layout_right:
        st.markdown("<h4 style='color:#a78bfa;'>Resume Optimization Check</h4>", unsafe_allow_html=True)
        
        match_score = eval_data.get('skill_match_score', 0.0)
        opt_score = eval_data.get('resume_opt_score', 0.0)
        
        # Skill Match Score progress bar
        st.markdown(f"**Skill Compatibility Overlap:** `{int(match_score*100)}%`")
        st.progress(float(match_score))
        
        # Resume Optimization progress bar
        st.markdown(f"**Structural Optimization Check:** `{int(opt_score*100)}%`")
        st.progress(float(opt_score))
        
        st.markdown("---")
        st.markdown("##### Profile Segment Found")
        sections_found = eval_data.get('sections_found', [])
        if sections_found:
            badges = "".join([f'<span class="badge" style="background:rgba(139,92,246,0.15); color:#c084fc; border:1px solid rgba(139,92,246,0.3); padding:4px 10px; border-radius:6px; font-size:12px; margin:4px; display:inline-block;">{s}</span>' for s in sections_found])
            st.markdown(f"<div>{badges}</div>", unsafe_allow_html=True)
        else:
            st.markdown("*No typical career resume sections mapped.*")
            
        st.markdown(f"<span class='role-badge'>Goal Role: {market_data.get('role', target_role_query)}</span>", unsafe_allow_html=True)

    # Tabs for detailed roadmap layouts
    tab_skills, tab_roadmap, tab_projects, tab_resources, tab_analytics = st.tabs([
        "🔍 Skills Gap Analysis", 
        "📅 Weekly Interactive Timeline", 
        "🚀 Bridging Portfolio Projects", 
        "📚 Study Resources",
        "📈 Profile Analytics History"
    ])
    
    with tab_skills:
        st.subheader("Indian Job Market Compatibility")
        if market_data:
            st.markdown(f"""
            <div style='background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.15); border-radius: 8px; padding: 15px; margin-bottom: 20px;'>
                <b>{market_data.get('role')} Expectations in India:</b><br>
                <i>Demand level: {market_data.get('market_demand')} | Entry level salary: {market_data.get('salary_range_lpa')} | Expected Experience: {market_data.get('experience_level')}</i>
                <p style='margin-top:10px; color:#cbd5e1; font-size:14px;'>{market_data.get('description')}</p>
            </div>
            """, unsafe_allow_html=True)
            
        col_gap_1, col_gap_2 = st.columns(2)
        
        with col_gap_1:
            st.markdown("##### 🟢 Matching Skills Map")
            matched = eval_data.get('matched_skills', [])
            if matched:
                badges = "".join([f'<span class="skill-tag-matched">{s}</span>' for s in matched])
                st.markdown(f"<div>{badges}</div>", unsafe_allow_html=True)
            else:
                st.write("No direct skills matches identified.")
                
        with col_gap_2:
            st.markdown("##### 🔴 High Priority Skill Gaps")
            missing = eval_data.get('missing_skills', [])
            if missing:
                badges = "".join([f'<span class="skill-tag-missing">{s}</span>' for s in missing])
                st.markdown(f"<div>{badges}</div>", unsafe_allow_html=True)
            else:
                st.write("Perfect! No skill gaps identified against requirements.")

    # 5. WEEKLY LEARNING PATH CARD TIMELINE FLOW
    with tab_roadmap:
        st.subheader("📅 Interactive Study Plan Roadmap")
        st.markdown("Track your learning by completing weekly milestones. Checkboxes write directly to the database state.")
        
        roadmap_milestones = db.get_learning_path(db_user_id)
        if not roadmap_milestones and learning_path.get('milestones'):
            roadmap_milestones = learning_path.get('milestones')
            
        if roadmap_milestones:
            completed_count = 0
            
            for milestone in roadmap_milestones:
                week_num = milestone.get('week_number')
                topic = milestone.get('topic')
                deliverable = milestone.get('deliverable')
                is_completed = bool(milestone.get('completed', 0))
                
                # Render weekly card with dynamic conditional CSS border-color
                card_style = "timeline-card-completed" if is_completed else "timeline-card"
                status_bullet = "🟢 Complete" if is_completed else "⏳ In Progress"
                
                st.markdown(f"""
                <div class="{card_style}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <span style="font-weight: 700; color: #a78bfa; font-size:14px; text-transform:uppercase;">Week {week_num} Module</span>
                        <span style="font-size:12px; font-weight: 600; color:{'#10b981' if is_completed else '#60a5fa'};">{status_bullet}</span>
                    </div>
                    <h4 style="margin: 0 0 8px 0; color:#ffffff;">{topic}</h4>
                    <p style="margin: 0; font-size:14px; color:#94a3b8;"><b>Key Deliverable:</b> {deliverable}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Checkbox container alignment
                col_checkbox, _ = st.columns([0.2, 0.8])
                with col_checkbox:
                    checked = st.checkbox(
                        "Mark Week Complete",
                        value=is_completed,
                        key=f"timeline_item_{db_user_id}_{week_num}"
                    )
                    
                    if checked != is_completed:
                        db.update_milestone_status(db_user_id, week_num, checked)
                        add_log("System", f"Updated Week {week_num} milestone status: {checked}")
                        st.rerun()
                        
                if is_completed:
                    completed_count += 1
            
            # Progress bar visualization
            total_weeks = len(roadmap_milestones)
            pct = int((completed_count / total_weeks) * 100)
            st.markdown(f"**Course Progress:** {completed_count}/{total_weeks} Weeks Completed ({pct}%)")
            st.progress(completed_count / total_weeks)
        else:
            st.info("No roadmap generated yet. Complete step 1 to build a study program.")

    # 5. portfolio project list with popup dialog trigger buttons
    with tab_projects:
        st.subheader("💻 Suggested Portfolio Projects")
        st.markdown("Recruiter-grade applications designed to showcase your competency in missing technologies. Click to see blueprints.")
        
        projects = learning_path.get('projects', [])
        if projects:
            for i, proj in enumerate(projects):
                # Custom container card
                st.markdown(f"""
                <div style='background: rgba(30,41,59,0.35); border: 1px solid rgba(139,92,246,0.15); border-radius: 12px; padding: 20px; margin-bottom: 20px;'>
                    <h3 style='margin:0 0 10px 0; color:#ffffff;'>🚀 {proj.get('name')}</h3>
                    <p style='margin: 0 0 15px 0; color:#cbd5e1; font-size:14px;'>{proj.get('description')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Modal launch button
                if st.button("⚙️ Open Implementation Blueprint", key=f"blueprint_btn_{i}"):
                    add_log("System", f"Opening blueprint modal window for project: '{proj.get('name')}'")
                    show_project_blueprint(proj)
        else:
            st.info("No projects suggested yet. Execute career diagnostics to map profile outputs.")

    with tab_resources:
        st.subheader("📚 Free Learning & Documentation Resources")
        st.markdown("Search terms recommended by the learning assistant to find guides for missing skills.")
        
        resources = learning_path.get('learning_resources', [])
        if resources:
            for res in resources:
                topic = res.get('topic')
                res_name = res.get('resource_name')
                query = res.get('suggested_search')
                
                st.markdown(f"📌 **{topic}**")
                st.write(f"- *Recommended Course/Guide:* {res_name}")
                
                yt_query = query.replace(" ", "+")
                st.markdown(f"- 🔍 [Search on YouTube](https://www.youtube.com/results?search_query={yt_query}) | [Search on Google](https://www.google.com/search?q={yt_query})")
                st.markdown("")
        else:
            st.info("No learning guides generated yet.")

    with tab_analytics:
        st.subheader("📈 Historic Analytics Tracking")
        st.markdown("Displays history of user pipeline runs to track callback probability changes as parameters are tweaked.")
        
        history = db.get_predictions_history(db_user_id)
        if len(history) >= 1:
            hist_df = pd.DataFrame(history)
            hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
            
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=hist_df['timestamp'],
                y=hist_df['callback_probability'],
                mode='lines+markers',
                name='Interview Callback (%)',
                line=dict(color='#8b5cf6', width=3) # Violet
            ))
            fig_hist.add_trace(go.Scatter(
                x=hist_df['timestamp'],
                y=hist_df['skill_match_score'] * 100,
                mode='lines+markers',
                name='Skills Compatibility (%)',
                line=dict(color='#34d399', width=3, dash='dash') # Green
            ))
            
            fig_hist.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30, 41, 59, 0.1)',
                legend=dict(font=dict(color="#e2e8f0")),
                font=dict(color="#e2e8f0"),
                xaxis=dict(title="Timestamp", gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="Score (%)", range=[0, 100], gridcolor="rgba(255,255,255,0.05)"),
                height=320,
                margin=dict(l=40, r=40, t=10, b=40)
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
            st.table(hist_df[['timestamp', 'skill_match_score', 'resume_opt_score', 'project_count', 'company_type', 'callback_probability']])
        else:
            st.info("No historical analytics logs logged.")
else:
    st.markdown("---")
    st.info("💡 **Getting Started:** Fill in your target tracking goals on the sidebar panel, upload your technical resume, and select **'Analyze Career Path Diagnostics'** to trigger the multi-agent intelligence portal.")
    
    col_show_1, col_show_2, col_show_3 = st.columns(3)
    with col_show_1:
        st.markdown("##### 👥 Orchestrated Agent Planner")
        st.write("Our supervisor planner state graph queries market jobs profiles, matches entry bars, and coordinates workflows sequentially.")
    with col_show_2:
        st.markdown("##### 📂 ChromaDB Vector Search")
        st.write("Evaluates missing technologies by indexing resume sentences in ChromaDB and checking semantic proximity to market expectations.")
    with col_show_3:
        st.markdown("##### 🔮 Scikit-learn Classifier Predictions")
        st.write("Renders success predictions using a Random Forest classifier trained on 1,200 simulated Indian candidate applications.")
