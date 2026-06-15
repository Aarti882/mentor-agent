import json
from pydantic import BaseModel, Field
from typing import List
from utils.helpers import call_gemini

class MarketResearchData(BaseModel):
    role: str = Field(description="The target job role analyzed")
    hard_skills: List[str] = Field(description="List of core technical/hard skills required for the role in India")
    tools: List[str] = Field(description="List of software tools, frameworks, and databases required")
    experience_level: str = Field(description="Expected experience range in years for Indian graduates")
    salary_range_lpa: str = Field(description="Expected entry-level to mid-level salary range in Lakhs Per Annum (LPA) in India")
    market_demand: str = Field(description="Current market demand level (e.g., High, Medium, Trending, Emerging)")
    description: str = Field(description="A brief description of what a professional in this role does in the Indian market")

# High-quality fallback data for Indian MCA context
FALLBACK_MARKET_DATA = {
    "Data Analyst": {
        "role": "Data Analyst",
        "hard_skills": ["SQL", "Python", "Pandas", "NumPy", "Statistics", "Data Visualization", "Excel", "Data Cleaning"],
        "tools": ["Tableau", "Power BI", "PostgreSQL", "Jupyter Notebook", "MS Excel", "Git"],
        "experience_level": "0 - 2 years",
        "salary_range_lpa": "4 - 8 LPA",
        "market_demand": "High",
        "description": "Analyzes raw business data to extract insights, create dashboards, and write database queries to assist business decision-making."
    },
    "ML Engineer": {
        "role": "ML Engineer",
        "hard_skills": ["Python", "Scikit-Learn", "Deep Learning", "TensorFlow", "PyTorch", "NLP", "Feature Engineering", "API Deployment"],
        "tools": ["Jupyter Notebook", "Docker", "Git", "FastAPI", "Flask", "MLflow", "AWS"],
        "experience_level": "1 - 3 years",
        "salary_range_lpa": "6 - 15 LPA",
        "market_demand": "Trending",
        "description": "Designs, builds, trains, and deploys machine learning models to production systems. Combines software engineering with data science."
    },
    "Agentic AI Developer": {
        "role": "Agentic AI Developer",
        "hard_skills": ["Python", "LangChain", "LangGraph", "Vector Databases", "Retrieval-Augmented Generation (RAG)", "Prompt Engineering", "Multi-Agent Systems", "Tool Calling"],
        "tools": ["ChromaDB", "Pinecone", "Gemini API", "OpenAI API", "Streamlit", "Git", "Docker", "HuggingFace"],
        "experience_level": "0 - 2 years",
        "salary_range_lpa": "7 - 18 LPA",
        "market_demand": "High",
        "description": "Develops autonomous AI systems that use LLMs, vector search, tool calling, and workflow graphs to perform complex multi-step workflows."
    }
}

def get_market_requirements(role: str, api_key: str = None) -> dict:
    """Gathers real-time or high-quality simulated job market data for the target role in India."""
    # Normalise role name to find fallback match
    matched_fallback_key = None
    for key in FALLBACK_MARKET_DATA:
        if key.lower() in role.lower() or role.lower() in key.lower():
            matched_fallback_key = key
            break
            
    # Attempt to query Gemini for real-time market search simulation
    if api_key:
        prompt = f"""
        Act as a job market research analyst for the tech sector in India (targeting Naukri, LinkedIn, and Wellfound contexts).
        Gather details on what recruiters are looking for when hiring for the role: '{role}' in India.
        Provide accurate lists of essential hard skills and tools that are in demand right now, entry-level experience requirements, average entry salary ranges in LPA, and market demand status.
        """
        try:
            response_text = call_gemini(
                prompt=prompt,
                api_key=api_key,
                system_instruction="You are a specialized Market Research Agent. Return details strictly in the JSON format matching the schema.",
                response_schema=MarketResearchData
            )
            data = json.loads(response_text)
            return data
        except Exception as e:
            print(f"Market Research Agent LLM call failed, returning fallback: {e}")
            
    # Return fallback data if API key is not present or LLM call fails
    if matched_fallback_key:
        return FALLBACK_MARKET_DATA[matched_fallback_key]
    
    # Generic fallback if the role is totally customized
    return {
        "role": role,
        "hard_skills": ["Python", "SQL", "Data Structures", "Algorithms", "Software Engineering Principles"],
        "tools": ["Git", "Docker", "GitHub", "Jupyter Notebook"],
        "experience_level": "0 - 2 years",
        "salary_range_lpa": "4 - 8 LPA",
        "market_demand": "Emerging",
        "description": f"Software development and domain engineering for {role} roles."
    }
