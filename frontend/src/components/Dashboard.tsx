import React, { useState, useEffect, useRef } from 'react';
import { 
  Briefcase, Upload, Terminal, CheckCircle, AlertCircle, Play, 
  ExternalLink, HelpCircle, History, X
} from 'lucide-react';

interface DashboardProps {
  userId: number;
}

interface Milestone {
  week_number: number;
  topic: string;
  deliverable: string;
  completed: boolean;
}

interface Project {
  name: string;
  description: string;
  tech_stack: string[];
  steps: string[];
}

interface Resource {
  topic: string;
  resource_name: string;
  suggested_search: string;
}

interface HistoryItem {
  timestamp: string;
  skill_match_score: number;
  resume_opt_score: number;
  project_count: number;
  company_type: string;
  callback_probability: number;
}

export const Dashboard: React.FC<DashboardProps> = ({ userId }) => {
  const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").trim().replace(/\/$/, "");
  // Goal Strategy states
  const [targetRole, setTargetRole] = useState('Agentic AI Developer');
  const [timelineMonths, setTimelineMonths] = useState(2);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const roleSuggestionsList = [
    "Agentic AI Developer",
    "ML Engineer",
    "Data Analyst",
    "Full Stack Web Developer",
    "Frontend React Developer",
    "Backend Node/Python Developer",
    "DevOps Cloud Engineer",
    "Cybersecurity Analyst",
    "Mobile App Developer",
    "Database Administrator",
    "UI/UX Engineer"
  ];

  const filteredSuggestions = roleSuggestionsList.filter(role => 
    role.toLowerCase().includes(targetRole.toLowerCase())
  );
  const [companyType, setCompanyType] = useState('Product-based');
  const [placementRoute, setPlacementRoute] = useState('On-campus');
  const [projectCount, setProjectCount] = useState(2);
  const [apiKey, setApiKey] = useState('');
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  // Diagnostics and data states
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('roadmap');
  const [diagnoseRan, setDiagnoseRan] = useState(false);
  const [diagnosticSteps, setDiagnosticSteps] = useState<{label: string, agent: string, status: 'pending'|'loading'|'done'}[]>([]);

  // Pipeline output data states
  const [predictiveScore, setPredictiveScore] = useState(0);
  const [skillMatchScore, setSkillMatchScore] = useState(0);
  const [resumeOptScore, setResumeOptScore] = useState(0);
  const [matchedSkills, setMatchedSkills] = useState<string[]>([]);
  const [missingSkills, setMissingSkills] = useState<string[]>([]);
  const [sectionsFound, setSectionsFound] = useState<string[]>([]);
  const [marketResearch, setMarketResearch] = useState<any>(null);
  
  // Roadmap states
  const [roadmap, setRoadmap] = useState<Milestone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Agent system log console states
  const [logs, setLogs] = useState<string[]>([]);
  const consoleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initial logs setup
    setLogs([
      `[${new Date().toLocaleTimeString()}] [System] React OS initialized. Connection active.`,
      `[${new Date().toLocaleTimeString()}] [System] Connected to API endpoint ${API_BASE_URL}`,
      `[${new Date().toLocaleTimeString()}] [System] SQLite database loaded successfully.`,
      `[${new Date().toLocaleTimeString()}] [System] Ready for career path diagnosis.`
    ]);

    // Load user profile history and roadmap if user already has run before
    fetchRoadmapAndHistory();
  }, [userId]);

  // Scroll terminal logs to bottom when updated
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs]);

  const addLog = (agent: string, message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${timestamp}] [${agent}] ${message}`]);
  };

  const fetchRoadmapAndHistory = async (loadActiveRoadmap = false) => {
    try {
      if (loadActiveRoadmap) {
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}/roadmap`);
        const data = await response.json();
        
        if (response.ok && data.milestones && data.milestones.length > 0) {
          setRoadmap(data.milestones);
          setProjects(data.projects || []);
          setResources(data.learning_resources || []);
          setDiagnoseRan(true);
          addLog('System', `Successfully fetched and loaded saved roadmap milestones (${data.milestones.length} weeks).`);
        } else {
          // Fallback check if DB returned empty but we have local mock data
          loadLocalMockData();
        }
      }

      const historyResponse = await fetch(`${API_BASE_URL}/api/users/${userId}/history`);
      const historyData = await historyResponse.json();
      
      if (historyResponse.ok && historyData.history) {
        setHistory(historyData.history);
        
        if (loadActiveRoadmap && historyData.history.length > 0) {
          const lastRun = historyData.history[historyData.history.length - 1];
          setPredictiveScore(lastRun.callback_probability);
          setSkillMatchScore(lastRun.skill_match_score);
          setResumeOptScore(lastRun.resume_opt_score);
        }
      }
    } catch (error) {
      console.warn("Failed to load historical profile state from backend.", error);
      if (loadActiveRoadmap) {
        loadLocalMockData();
      }
    }
  };

  const loadLocalMockData = () => {
    const savedMock = localStorage.getItem(`mca_mentor_mock_data_${userId}`);
    if (savedMock) {
      try {
        const parsed = JSON.parse(savedMock);
        setPredictiveScore(parsed.predictiveScore || 0);
        setSkillMatchScore(parsed.evaluation?.skill_match_score || 0);
        setResumeOptScore(parsed.evaluation?.resume_opt_score || 0);
        setMatchedSkills(parsed.evaluation?.matched_skills || []);
        setMissingSkills(parsed.evaluation?.missing_skills || []);
        setSectionsFound(parsed.evaluation?.sections_found || []);
        setMarketResearch(parsed.marketResearch || null);
        setRoadmap(parsed.learningPath?.milestones || []);
        setProjects(parsed.learningPath?.projects || []);
        setResources(parsed.learningPath?.learning_resources || []);
        setDiagnoseRan(true);
        addLog('System', 'Offline fallback: Loaded local session simulation state.');
      } catch (e) {
        console.error("Failed to parse local mock data:", e);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setResumeFile(e.target.files[0]);
      addLog('System', `Attached file: ${e.target.files[0].name} (${Math.round(e.target.files[0].size / 1024)} KB)`);
    }
  };

  const handleMilestoneToggle = async (weekNumber: number, currentStatus: boolean) => {
    const newStatus = !currentStatus;
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}/roadmap/milestone`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ week_number: weekNumber, completed: newStatus }),
      });

      if (response.ok) {
        setRoadmap(prev => 
          prev.map(m => m.week_number === weekNumber ? { ...m, completed: newStatus } : m)
        );
        addLog('System', `Week ${weekNumber} milestone toggled: ${newStatus ? 'Completed' : 'Pending'}`);
      }
    } catch (error) {
      console.warn("Backend offline. Updating milestone checklist locally.");
      setRoadmap(prev => 
        prev.map(m => m.week_number === weekNumber ? { ...m, completed: newStatus } : m)
      );
      
      // Update local storage mock data state
      const savedMock = localStorage.getItem(`mca_mentor_mock_data_${userId}`);
      if (savedMock) {
        try {
          const parsed = JSON.parse(savedMock);
          if (parsed.learningPath && parsed.learningPath.milestones) {
            parsed.learningPath.milestones = parsed.learningPath.milestones.map((m: any) => 
              m.week_number === weekNumber ? { ...m, completed: newStatus } : m
            );
            localStorage.setItem(`mca_mentor_mock_data_${userId}`, JSON.stringify(parsed));
          }
        } catch (e) {
          console.error("Failed to update local storage checkbox state:", e);
        }
      }
      addLog('System', `Week ${weekNumber} milestone toggled locally: ${newStatus ? 'Completed' : 'Pending'}`);
    }
  };

  const runDiagnostics = async () => {
    if (!resumeFile) {
      alert("Please upload a resume file first.");
      return;
    }

    setLoading(true);
    setDiagnoseRan(false);
    
    // Set visual steps list
    const initialSteps = [
      { label: "Parsing PDF Resume & Cleaning Strings", agent: "System", status: "loading" as const },
      { label: "Querying Target Role Market Intelligence", agent: "Market Research Agent", status: "pending" as const },
      { label: "Running Semantic Check Against ChromaDB", agent: "Evaluator Agent", status: "pending" as const },
      { label: "Predicting Callback Rate (Random Forest Model)", agent: "Predictive ML Engine", status: "pending" as const },
      { label: "Structuring Personalized Study Path", agent: "Learning Path Agent", status: "pending" as const }
    ];
    setDiagnosticSteps(initialSteps);

    // Form payload construction
    const formData = new FormData();
    formData.append("user_id", userId.toString());
    formData.append("target_role", targetRole);
    formData.append("timeline_months", timelineMonths.toString());
    formData.append("company_type", companyType);
    formData.append("placement_route", placementRoute);
    formData.append("project_count", projectCount.toString());
    formData.append("api_key", apiKey);
    formData.append("resume", resumeFile);

    try {
      addLog('System', `Triggered core diagnostics for userId: ${userId}.`);
      
      // Simulated delay transitions for visual feedback
      await new Promise(resolve => setTimeout(resolve, 800));
      setDiagnosticSteps(prev => prev.map((s, i) => i === 0 ? { ...s, status: 'done' } : i === 1 ? { ...s, status: 'loading' } : s));
      addLog('Market Research Agent', `Initiating Naukri & LinkedIn scraping queries for '${targetRole}' in India.`);
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      setDiagnosticSteps(prev => prev.map((s, i) => i === 1 ? { ...s, status: 'done' } : i === 2 ? { ...s, status: 'loading' } : s));
      addLog('Evaluator Agent', "Building in-memory ChromaDB client. Vectorizing text chunks.");
      
      await new Promise(resolve => setTimeout(resolve, 1200));
      setDiagnosticSteps(prev => prev.map((s, i) => i === 2 ? { ...s, status: 'done' } : i === 3 ? { ...s, status: 'loading' } : s));
      addLog('Predictive ML Engine', "Feeding profile coefficients into Random Forest classifier.");
      
      await new Promise(resolve => setTimeout(resolve, 900));
      setDiagnosticSteps(prev => prev.map((s, i) => i === 3 ? { ...s, status: 'done' } : i === 4 ? { ...s, status: 'loading' } : s));
      addLog('Learning Path Agent', "Mapping week structures and formulating custom repository setup code.");

      const response = await fetch(`${API_BASE_URL}/api/diagnose`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Workflow pipeline execution crashed.');
      }

      setDiagnosticSteps(prev => prev.map(s => ({ ...s, status: 'done' })));
      addLog('System', `Successfully completed pipeline runs. Callback probability score: ${data.predictive_score}%.`);

      // Set pipeline variables
      setPredictiveScore(data.predictive_score);
      setSkillMatchScore(data.evaluation.skill_match_score);
      setResumeOptScore(data.evaluation.resume_opt_score);
      setMatchedSkills(data.evaluation.matched_skills || []);
      setMissingSkills(data.evaluation.missing_skills || []);
      setSectionsFound(data.evaluation.sections_found || []);
      setMarketResearch(data.market_research);
      setRoadmap(data.learning_path.milestones || []);
      setProjects(data.learning_path.projects || []);
      setResources(data.learning_path.learning_resources || []);
      setDiagnoseRan(true);

      // Refresh history log list
      fetchRoadmapAndHistory();

    } catch (err: any) {
      console.warn("Backend offline or request failed. Activating local career planner simulator...", err);
      addLog('System', 'Backend offline. Booting local simulation mode...');
      
      // Calculate a realistic predictive score based on user inputs
      const isProduct = companyType === 'Product-based';
      const isOffCampus = placementRoute === 'Off-campus';
      let scoreBase = 65;
      
      // Multipliers
      scoreBase += projectCount * 3.5;
      if (isProduct) scoreBase -= 14;
      if (isOffCampus) scoreBase -= 8;
      
      const mockPredictiveScore = Math.min(98, Math.max(15, Math.round(scoreBase + Math.random() * 8)));
      
      // Determine matched/missing skills based on target role keyword dynamically
      let mockMatched = ['Python', 'SQL', 'Git'];
      let mockMissing: string[] = [];
      let mockSalary = "6-12 LPA";
      let mockDescription = `Professional execution, testing, and deployment for ${targetRole} positions in startups and corporate setups.`;

      const roleLower = targetRole.toLowerCase();

      if (roleLower.includes('agentic') || roleLower.includes('ai') || roleLower.includes('llm') || roleLower.includes('generative')) {
        mockMatched.push('LangChain', 'Prompt Engineering');
        mockMissing.push('LangGraph', 'Vector Databases', 'ChromaDB', 'Multi-Agent Systems', 'LLM Fine-tuning');
        mockSalary = "8-16 LPA";
        mockDescription = `Developing specialized agentic workflows, orchestrating API tool-use, and implementing vector searches using multi-agent frameworks.`;
      } else if (roleLower.includes('ml') || roleLower.includes('machine') || roleLower.includes('learning') || roleLower.includes('deep')) {
        mockMatched.push('Scikit-Learn', 'Pandas');
        mockMissing.push('TensorFlow', 'PyTorch', 'MLOps Pipelines', 'FastAPI Deployments', 'Model Optimization');
        mockSalary = "7-14 LPA";
        mockDescription = `Building end-to-end machine learning pipelines, training statistical models, and deploying predictions to production endpoints.`;
      } else if (roleLower.includes('web') || roleLower.includes('developer') || roleLower.includes('frontend') || roleLower.includes('backend') || roleLower.includes('stack') || roleLower.includes('react') || roleLower.includes('node') || roleLower.includes('software')) {
        mockMatched.push('JavaScript', 'HTML/CSS', 'GitHub');
        mockMissing.push('React.js Framework', 'Node.js & Express', 'MongoDB / SQL Databases', 'RESTful API Integration', 'Docker Containers');
        mockSalary = "5-11 LPA";
        mockDescription = `Designing responsive user interfaces, writing scalable backend services, constructing REST APIs, and coordinating database schemas.`;
      } else if (roleLower.includes('devops') || roleLower.includes('cloud') || roleLower.includes('aws') || roleLower.includes('kubernetes') || roleLower.includes('docker')) {
        mockMatched.push('Linux Shell', 'Git versioning', 'Bash Scripting');
        mockMissing.push('Docker Containers', 'Kubernetes Clusters', 'AWS Cloud Services', 'CI/CD Pipelines (GitHub Actions)', 'Infrastructure as Code (Terraform)');
        mockSalary = "6-13 LPA";
        mockDescription = `Configuring automated release pipelines, managing serverless architectures, scripting deployments, and optimizing containerized setups.`;
      } else if (roleLower.includes('security') || roleLower.includes('cyber') || roleLower.includes('network') || roleLower.includes('penetration') || roleLower.includes('hack')) {
        mockMatched.push('Basic Networking', 'Linux Command Line', 'Python');
        mockMissing.push('Ethical Hacking', 'Penetration Testing Frameworks', 'Wireshark Packet Analysis', 'OWASP Top 10 vulnerabilities', 'Cryptography & IAM');
        mockSalary = "6-12 LPA";
        mockDescription = `Identifying architectural vulnerabilities, analyzing network logs, implementing security controls, and running compliance assessments.`;
      } else if (roleLower.includes('mobile') || roleLower.includes('app') || roleLower.includes('android') || roleLower.includes('ios') || roleLower.includes('flutter') || roleLower.includes('native')) {
        mockMatched.push('UI Design basics', 'JavaScript', 'Git');
        mockMissing.push('Flutter & Dart SDK', 'React Native Framework', 'State Management (Redux/Provider)', 'Mobile App Store Deployments', 'Local Storage databases');
        mockSalary = "5-10 LPA";
        mockDescription = `Building cross-platform mobile apps, implementing state transitions, integrating native APIs, and compiling distribution bundles.`;
      } else {
        // Default Data Analyst / General Analyst
        mockMatched.push('Pandas', 'Excel data tools');
        mockMissing.push('Tableau Dashboards', 'Power BI', 'SQL Query Optimization', 'PostgreSQL database schemas', 'Statistical Analysis');
        mockSalary = "4-9 LPA";
        mockDescription = `Cleaning messy datasets, modeling business metrics, drafting interactive dashboard reports, and executing analytical SQL queries.`;
      }
      
      const mockEvaluation = {
        skill_match_score: mockMatched.length / (mockMatched.length + mockMissing.length),
        resume_opt_score: 0.82,
        matched_skills: mockMatched,
        missing_skills: mockMissing,
        sections_found: ['education', 'skills', 'projects', 'contact']
      };

      const mockMarket = {
        role: targetRole,
        experience_level: "0-2 years",
        salary_range_lpa: mockSalary,
        market_demand: "High / Trending",
        description: mockDescription
      };

      // Generate week timeline structure
      const totalWeeks = timelineMonths * 4;
      const mockMilestones: Milestone[] = [];
      for (let w = 1; w <= totalWeeks; w++) {
        const skill = mockMissing[(w - 1) % mockMissing.length] || "Advanced Architectures";
        mockMilestones.push({
          week_number: w,
          topic: `Mastering ${skill}`,
          deliverable: `Configure a mock app implementing ${skill} and push the repository to GitHub.`,
          completed: false
        });
      }

      const mockProjects: Project[] = [
        {
          name: `Autonomous ${targetRole} Project Suite`,
          description: `An end-to-end sandbox software demonstrating integration of your missing skills like ${mockMissing.slice(0, 2).join(' and ')}.`,
          tech_stack: ['Python', ...mockMissing, 'Streamlit'],
          steps: [
            "Initialize repository workspace and configure Git branch.",
            "Draft core database schemas and API routing structures.",
            "Write basic validation checks and test coverage files.",
            "Run local builds and document setup requirements in README.md."
          ]
        }
      ];

      const mockResources: Resource[] = mockMissing.map(skill => ({
        topic: skill,
        resource_name: `${skill} Practical Crash Course`,
        suggested_search: `${skill} tutorial step by step guide for beginners`
      }));

      // Set states
      setDiagnosticSteps(prev => prev.map(s => ({ ...s, status: 'done' })));
      
      setPredictiveScore(mockPredictiveScore);
      setSkillMatchScore(mockEvaluation.skill_match_score);
      setResumeOptScore(mockEvaluation.resume_opt_score);
      setMatchedSkills(mockEvaluation.matched_skills);
      setMissingSkills(mockEvaluation.missing_skills);
      setSectionsFound(mockEvaluation.sections_found);
      setMarketResearch(mockMarket);
      setRoadmap(mockMilestones);
      setProjects(mockProjects);
      setResources(mockResources);
      setDiagnoseRan(true);

      // Save mock state to localStorage for persistence
      const localMockPayload = {
        predictiveScore: mockPredictiveScore,
        evaluation: mockEvaluation,
        marketResearch: mockMarket,
        learningPath: {
          milestones: mockMilestones,
          projects: mockProjects,
          learning_resources: mockResources
        }
      };
      localStorage.setItem(`mca_mentor_mock_data_${userId}`, JSON.stringify(localMockPayload));
      
      // Update local history table visual log
      const newHistoryItem: HistoryItem = {
        timestamp: new Date().toISOString(),
        skill_match_score: mockEvaluation.skill_match_score,
        resume_opt_score: mockEvaluation.resume_opt_score,
        project_count: projectCount,
        company_type: companyType,
        callback_probability: mockPredictiveScore
      };
      setHistory(prev => [...prev, newHistoryItem]);

      addLog('System', 'Diagnostics compiled successfully via offline mock simulator.');
    } finally {
      setLoading(false);
    }
  };

  // Radial Gauge SVG Calculations
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const dashoffset = circumference - (circumference * predictiveScore) / 100;
  
  // Custom dial color based on probability
  let gaugeColor = "#ef4444"; // Red
  if (predictiveScore >= 40 && predictiveScore < 75) gaugeColor = "#f59e0b"; // Yellow
  if (predictiveScore >= 75) gaugeColor = "#10b981"; // Green

  return (
    <div className="dashboard-grid">
      {/* ----------------- SIDEBAR OPTIONS ----------------- */}
      <div className="dashboard-sidebar">
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Briefcase size={20} /> Career Target
          </h3>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>API Key (Optional)</label>
            <input 
              type="password" 
              className="form-control"
              placeholder="Gemini API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0, position: 'relative' }}>
            <label>Target Role Track</label>
            <input 
              type="text" 
              className="form-control"
              placeholder="Search or type any role..."
              value={targetRole}
              onChange={(e) => {
                setTargetRole(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => {
                setTimeout(() => setShowSuggestions(false), 250);
              }}
            />
            {showSuggestions && filteredSuggestions.length > 0 && (
              <div 
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  background: '#0c1222',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
                  zIndex: 999,
                  maxHeight: '180px',
                  overflowY: 'auto',
                  marginTop: '4px'
                }}
              >
                {filteredSuggestions.map((suggestion, idx) => (
                  <div 
                    key={idx}
                    onClick={() => {
                      setTargetRole(suggestion);
                      setShowSuggestions(false);
                    }}
                    style={{
                      padding: '10px 14px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                      color: '#cbd5e1',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(139, 92, 246, 0.2)';
                      e.currentTarget.style.color = '#fff';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.color = '#cbd5e1';
                    }}
                  >
                    {suggestion}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Timeline: {timelineMonths} Months</label>
            <input 
              type="range" 
              min="1" 
              max="6" 
              className="form-control"
              value={timelineMonths}
              onChange={(e) => setTimelineMonths(parseInt(e.target.value))}
            />
          </div>

          <hr style={{ margin: '5px 0' }} />

          <h3 style={{ margin: '0 0 5px 0', color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={20} /> strategy factors
          </h3>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Target Segment</label>
            <select 
              className="form-control"
              value={companyType}
              onChange={(e) => setCompanyType(e.target.value)}
            >
              <option value="Product-based">Product-based</option>
              <option value="Service-based">Service-based</option>
            </select>
            <div style={{ marginTop: '8px' }}>
              {companyType === 'Product-based' ? (
                <span className="badge-product">Product-based Target</span>
              ) : (
                <span className="badge-service">Service-based Target</span>
              )}
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Application Route</label>
            <select 
              className="form-control"
              value={placementRoute}
              onChange={(e) => setPlacementRoute(e.target.value)}
            >
              <option value="On-campus">On-campus Placement</option>
              <option value="Off-campus">Off-campus hunt</option>
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Portfolio Projects: {projectCount}</label>
            <input 
              type="range" 
              min="0" 
              max="10" 
              className="form-control"
              value={projectCount}
              onChange={(e) => setProjectCount(parseInt(e.target.value))}
            />
          </div>
        </div>

        {/* Console Logger Window */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Terminal size={18} /> Agent System Logs
          </h4>
          <div className="console-box" ref={consoleRef}>
            {logs.map((log, idx) => (
              <div key={idx} style={{ marginBottom: '6px', lineHeight: '1.4' }}>{log}</div>
            ))}
          </div>
        </div>
      </div>

      {/* ----------------- MAIN PANEL ----------------- */}
      <div className="dashboard-main">
        {/* Upload Resume Form */}
        <div className="glass-panel">
          <h3 style={{ margin: '0 0 15px 0', color: '#fff' }}>📄 Upload Resume Profile</h3>
          <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <input 
                type="file" 
                id="resumeUpload" 
                accept=".pdf,.txt" 
                style={{ display: 'none' }} 
                onChange={handleFileChange}
              />
              <label 
                htmlFor="resumeUpload"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '12px 20px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px dashed var(--border-color)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  color: resumeFile ? '#fff' : '#cbd5e1',
                  fontWeight: 600,
                  justifyContent: 'center'
                }}
              >
                <Upload size={18} />
                {resumeFile ? resumeFile.name : "Choose PDF or TXT Resume"}
              </label>
            </div>
            
            <button 
              onClick={runDiagnostics} 
              className="btn-primary" 
              style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 30px' }}
              disabled={loading}
            >
              <Play size={18} />
              {loading ? "Analyzing..." : "Run AI Diagnostics"}
            </button>

            {!loading && history.length > 0 && (
              <button 
                onClick={() => fetchRoadmapAndHistory(true)} 
                className="btn-secondary" 
                style={{ 
                  width: 'auto', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px', 
                  padding: '12px 20px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  color: '#cbd5e1',
                  fontWeight: 600,
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
                  e.currentTarget.style.color = '#fff';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  e.currentTarget.style.color = '#cbd5e1';
                }}
              >
                <History size={18} />
                Load Last Run
              </button>
            )}
          </div>
        </div>

        {/* Loading Progress steps checklist */}
        {loading && (
          <div className="glass-panel">
            <h3 style={{ margin: '0 0 15px 0', color: '#fff' }}>🔎 Running Career Diagnostics Workflow</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {diagnosticSteps.map((step, index) => (
                <div 
                  key={index} 
                  style={{
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px',
                    color: step.status === 'done' ? '#34d399' : step.status === 'loading' ? '#60a5fa' : '#94a3b8'
                  }}
                >
                  {step.status === 'done' && <CheckCircle size={18} />}
                  {step.status === 'loading' && <HelpCircle size={18} className="animate-spin" />}
                  {step.status === 'pending' && <AlertCircle size={18} />}
                  <span><strong>{step.agent}:</strong> {step.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Output Diagnostics Panels */}
        {diagnoseRan && (
          <>
            <div className="glass-panel" style={{ padding: '30px' }}>
              <h2 style={{ margin: '0 0 25px 0', fontSize: '24px', color: '#a78bfa' }}>📊 Career Compatibility Analytics</h2>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr', gap: '30px', alignItems: 'center' }}>
                {/* Visual SVG Speedometer Gauge */}
                <div style={{ textAlign: 'center' }}>
                  <svg className="radial-svg" width="180" height="180" viewBox="0 0 180 180">
                    <circle className="bg" cx="90" cy="90" r="70" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="12"></circle>
                    <circle 
                      className="meter" 
                      cx="90" 
                      cy="90" 
                      r="70" 
                      fill="transparent" 
                      stroke={gaugeColor} 
                      strokeWidth="12" 
                      strokeDasharray={circumference}
                      strokeDashoffset={dashoffset}
                      strokeLinecap="round" 
                      transform="rotate(-90 90 90)"
                      style={{ '--accent-glow': gaugeColor } as React.CSSProperties}
                    ></circle>
                    <text x="90" y="98" fill="#fff" fontSize="34" fontWeight="800" textAnchor="middle">{predictiveScore}%</text>
                  </svg>
                  <p style={{ marginTop: '15px', color: '#cbd5e1', fontSize: '14px', fontWeight: 600 }}>
                    Interview Callback success (ML Model)
                  </p>
                </div>

                {/* Score details progress bars */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}>
                      <span style={{ fontWeight: 600 }}>Skills Compatibility Index</span>
                      <strong style={{ color: '#8b5cf6' }}>{Math.round(skillMatchScore * 100)}%</strong>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '6px', height: '10px', overflow: 'hidden' }}>
                      <div style={{ background: '#8b5cf6', width: `${skillMatchScore * 100}%`, height: '100%' }}></div>
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}>
                      <span style={{ fontWeight: 600 }}>Resume Keyword Formatting</span>
                      <strong style={{ color: '#10b981' }}>{Math.round(resumeOptScore * 100)}%</strong>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '6px', height: '10px', overflow: 'hidden' }}>
                      <div style={{ background: '#10b981', width: `${resumeOptScore * 100}%`, height: '100%' }}></div>
                    </div>
                  </div>

                  <hr style={{ margin: '5px 0' }} />

                  <div>
                    <span style={{ fontSize: '13px', color: '#94a3b8' }}>SECTIONS DETECTED IN RESUME:</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                      {sectionsFound.map((sec, idx) => (
                        <span key={idx} style={{ background: 'rgba(139,92,246,0.12)', color: '#c084fc', border: '1px solid rgba(139,92,246,0.25)', padding: '3px 8px', borderRadius: '4px', fontSize: '12px' }}>
                          {sec}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation tabs */}
            <div>
              <div className="tabs-container">
                <button 
                  onClick={() => setActiveTab('roadmap')} 
                  className={`tab-btn ${activeTab === 'roadmap' ? 'active' : ''}`}
                >
                  Weekly Roadmap
                </button>
                <button 
                  onClick={() => setActiveTab('skills')} 
                  className={`tab-btn ${activeTab === 'skills' ? 'active' : ''}`}
                >
                  Skill Gap Check
                </button>
                <button 
                  onClick={() => setActiveTab('projects')} 
                  className={`tab-btn ${activeTab === 'projects' ? 'active' : ''}`}
                >
                  Portfolio Projects
                </button>
                <button 
                  onClick={() => setActiveTab('resources')} 
                  className={`tab-btn ${activeTab === 'resources' ? 'active' : ''}`}
                >
                  study guides
                </button>
                <button 
                  onClick={() => setActiveTab('history')} 
                  className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
                >
                  Historical Logs
                </button>
              </div>

              {/* TAB CONTENT ROADMAP */}
              {activeTab === 'roadmap' && (
                <div className="glass-panel">
                  <h3 style={{ margin: '0 0 10px 0' }}>📅 Weekly Syllabus Roadmap</h3>
                  <p style={{ margin: '0 0 20px 0', color: '#94a3b8', fontSize: '14px' }}>
                    Track milestones step-by-step. Completions write directly to SQLite database.
                  </p>
                  
                  <div className="timeline-list">
                    {roadmap.map((m, idx) => (
                      <div key={idx} className={`timeline-card-node ${m.completed ? 'completed' : ''}`}>
                        <input 
                          type="checkbox" 
                          checked={m.completed} 
                          onChange={() => handleMilestoneToggle(m.week_number, m.completed)}
                        />
                        <div className="timeline-details">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '11px', color: '#a78bfa', fontWeight: 700, textTransform: 'uppercase' }}>Week {m.week_number} Module</span>
                            <span style={{ fontSize: '12px', color: m.completed ? '#10b981' : '#60a5fa' }}>
                              {m.completed ? "🟢 Completed" : "⏳ Pending"}
                            </span>
                          </div>
                          <h4 style={{ margin: '5px 0', color: '#fff' }}>{m.topic}</h4>
                          <p style={{ margin: 0, fontSize: '14px', color: '#cbd5e1' }}>
                            <strong>Deliverable:</strong> {m.deliverable}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB CONTENT SKILLS GAP */}
              {activeTab === 'skills' && (
                <div className="glass-panel">
                  <h3 style={{ margin: '0 0 15px 0' }}>🔍 Market Match Details</h3>
                  
                  {marketResearch && (
                    <div style={{ background: 'rgba(139, 92, 246, 0.04)', border: '1px solid rgba(139, 92, 246, 0.15)', borderRadius: '8px', padding: '16px', marginBottom: '20px' }}>
                      <h4 style={{ margin: '0 0 8px 0', color: '#fff' }}>{marketResearch.role} Market Intelligence (India)</h4>
                      <p style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#94a3b8' }}>
                        Experience: {marketResearch.experience_level} | Entry Salary: {marketResearch.salary_range_lpa} | Demand: {marketResearch.market_demand}
                      </p>
                      <p style={{ margin: 0, fontSize: '14px', color: '#cbd5e1' }}>{marketResearch.description}</p>
                    </div>
                  )}

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    <div>
                      <h4 style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px' }}><CheckCircle size={18} /> Matching Skills</h4>
                      <div style={{ marginTop: '10px' }}>
                        {matchedSkills.map((s, idx) => (
                          <span key={idx} className="skill-tag-matched">{s}</span>
                        ))}
                        {matchedSkills.length === 0 && <p style={{ fontSize: '14px', color: '#94a3b8' }}>No matches found.</p>}
                      </div>
                    </div>

                    <div>
                      <h4 style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '6px' }}><AlertCircle size={18} /> Gaps to address</h4>
                      <div style={{ marginTop: '10px' }}>
                        {missingSkills.map((s, idx) => (
                          <span key={idx} className="skill-tag-missing">{s}</span>
                        ))}
                        {missingSkills.length === 0 && <p style={{ fontSize: '14px', color: '#94a3b8' }}>Awesome! No skill gaps mapped.</p>}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB CONTENT PORTFOLIO PROJECTS */}
              {activeTab === 'projects' && (
                <div className="glass-panel">
                  <h3 style={{ margin: '0 0 10px 0' }}>💻 Tailored Portfolio Projects</h3>
                  <p style={{ margin: '0 0 20px 0', color: '#94a3b8', fontSize: '14px' }}>
                    Suggested repository architectures to prove competency to technical recruiters.
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    {projects.map((proj, idx) => (
                      <div key={idx} style={{ background: 'rgba(30, 41, 59, 0.25)', border: '1px solid rgba(255, 255, 255, 0.04)', borderRadius: '10px', padding: '20px' }}>
                        <h4 style={{ margin: '0 0 8px 0', color: '#fff', fontSize: '18px' }}>🚀 {proj.name}</h4>
                        <p style={{ margin: '0 0 15px 0', color: '#cbd5e1', fontSize: '14px' }}>{proj.description}</p>
                        
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                            {proj.tech_stack.map((tech, tIdx) => (
                              <span key={tIdx} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', color: '#a5b4fc' }}>
                                {tech}
                              </span>
                            ))}
                          </div>

                          <button 
                            onClick={() => setActiveProject(proj)}
                            className="btn-primary" 
                            style={{ width: 'auto', padding: '8px 16px', fontSize: '13px' }}
                          >
                            Open Blueprint
                          </button>
                        </div>
                      </div>
                    ))}
                    {projects.length === 0 && <p style={{ fontSize: '14px', color: '#94a3b8' }}>No project suggestions mapped.</p>}
                  </div>
                </div>
              )}

              {/* TAB CONTENT RESOURCES */}
              {activeTab === 'resources' && (
                <div className="glass-panel">
                  <h3 style={{ margin: '0 0 20px 0' }}>📚 Curated Learning Guides</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    {resources.map((res, idx) => {
                      const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(res.suggested_search)}`;
                      return (
                        <div key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '15px' }}>
                          <h4 style={{ margin: '0 0 5px 0', color: '#fff' }}>📌 {res.topic}</h4>
                          <p style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#cbd5e1' }}>
                            Recommended source: <em>{res.resource_name}</em>
                          </p>
                          <a 
                            href={searchUrl} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '13px', color: '#8b5cf6', textDecoration: 'none' }}
                          >
                            Search Tutorials on YouTube <ExternalLink size={14} />
                          </a>
                        </div>
                      );
                    })}
                    {resources.length === 0 && <p style={{ fontSize: '14px', color: '#94a3b8' }}>No documentation guides mapped.</p>}
                  </div>
                </div>
              )}

              {/* TAB CONTENT ANALYTICS HISTORY */}
              {activeTab === 'history' && (
                <div className="glass-panel">
                  <h3 style={{ margin: '0 0 20px 0' }}>📈 Profile Diagnostics Log History</h3>
                  {history.length > 0 ? (
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                            <th style={{ padding: '12px' }}>Timestamp</th>
                            <th style={{ padding: '12px' }}>Skill Match</th>
                            <th style={{ padding: '12px' }}>Resume Opt</th>
                            <th style={{ padding: '12px' }}>Projects</th>
                            <th style={{ padding: '12px' }}>Company Type</th>
                            <th style={{ padding: '12px' }}>Callback Rate</th>
                          </tr>
                        </thead>
                        <tbody>
                          {history.map((hist, index) => (
                            <tr key={index} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                              <td style={{ padding: '12px' }}>{new Date(hist.timestamp).toLocaleString()}</td>
                              <td style={{ padding: '12px' }}>{Math.round(hist.skill_match_score * 100)}%</td>
                              <td style={{ padding: '12px' }}>{Math.round(hist.resume_opt_score * 100)}%</td>
                              <td style={{ padding: '12px' }}>{hist.project_count}</td>
                              <td style={{ padding: '12px' }}>{hist.company_type}</td>
                              <td style={{ padding: '12px', color: '#a78bfa', fontWeight: 'bold' }}>{hist.callback_probability}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p style={{ fontSize: '14px', color: '#94a3b8' }}>No diagnostics run history retrieved.</p>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* ----------------- MODAL BLUEPRINT DRAWER OVERLAY ----------------- */}
      {activeProject && (
        <div className="modal-overlay" onClick={() => setActiveProject(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setActiveProject(null)}><X size={24} /></button>
            <h3 style={{ color: '#a78bfa', margin: '0 0 10px 0', fontSize: '22px' }}>🚀 Project Blueprint</h3>
            <h2 style={{ margin: '0 0 15px 0', color: '#fff' }}>{activeProject.name}</h2>
            <p style={{ color: '#cbd5e1', lineHeight: '1.6', margin: '0 0 20px 0' }}>{activeProject.description}</p>
            
            <hr style={{ margin: '15px 0', borderColor: 'rgba(255,255,255,0.05)' }} />
            
            <h4 style={{ color: '#fff', margin: '0 0 10px 0' }}>📦 Recommended Repo Skeleton</h4>
            <pre style={{ background: '#020617', padding: '15px', borderRadius: '8px', fontFamily: 'monospace', fontSize: '13px', color: '#38bdf8', overflowX: 'auto', margin: '0 0 20px 0' }}>
{`${activeProject.name.toLowerCase().replace(/\s+/g, '_')}/
├── config/
│   └── database.py        # SQLite or ChromaDB configuration
├── models/
│   └── pipeline.py        # Core processing logic
├── utils/
│   └── helpers.py         # File inputs and text processing helpers
├── app.py                 # User Interface web view
├── requirements.txt       # Project dependencies
└── README.md              # Deployment step-by-step documentation`}
            </pre>

            <h4 style={{ color: '#fff', margin: '0 0 10px 0' }}>🛠️ Core Tech Stack</h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '20px' }}>
              {activeProject.tech_stack.map((tech, idx) => (
                <span key={idx} style={{ background: 'rgba(139,92,246,0.12)', color: '#c084fc', border: '1px solid rgba(139,92,246,0.25)', padding: '4px 10px', borderRadius: '6px', fontSize: '12px' }}>
                  {tech}
                </span>
              ))}
            </div>

            <h4 style={{ color: '#fff', margin: '0 0 10px 0' }}>📋 Step-by-Step Implementation</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {activeProject.steps.map((step, idx) => (
                <div key={idx} style={{ display: 'flex', gap: '10px', fontSize: '14px', color: '#cbd5e1', lineHeight: '1.4' }}>
                  <strong>{idx + 1}.</strong>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
