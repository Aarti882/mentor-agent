import re
import chromadb
import uuid
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from utils.helpers import get_gemini_client

# Define a custom embedding function to make ChromaDB work offline or online
class MCAEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key=None):
        self.client = get_gemini_client(api_key)
        self.vocabulary = None
        
    def __call__(self, input_docs: Documents) -> Embeddings:
        # Online Mode: Use Gemini Embeddings
        if self.client:
            try:
                embeddings = []
                for doc in input_docs:
                    response = self.client.models.embed_content(
                        model="text-embedding-004",
                        contents=doc
                    )
                    # The response object has embeddings, which contain values
                    embedding_values = response.embedding.values
                    embeddings.append(embedding_values)
                return embeddings
            except Exception as e:
                print(f"Gemini embedding failed, falling back to local TF-IDF: {e}")
                # Fall through to offline mode
                
        # Offline Mode: Simple Bag-of-Words/TF-IDF hashing to 128 dimensions
        # This keeps the application completely standalone and fast
        embeddings = []
        for doc in input_docs:
            # Clean and split doc into words
            words = re.findall(r'\w+', doc.lower())
            vector = [0.0] * 128
            for w in words:
                # Simple hash function to map words to index 0-127
                idx = sum(ord(c) for c in w) % 128
                vector[idx] += 1.0
            
            # L2 Normalization of vector
            norm = sum(x**2 for x in vector)**0.5
            if norm > 0:
                vector = [x / norm for x in vector]
            embeddings.append(vector)
            
        return embeddings

def chunk_text(text, chunk_size=200, overlap=50):
    """Splits resume text into overlapping sentence/word chunks."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            # Keep overlap
            current_chunk = sentence
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return [c for c in chunks if len(c) > 5]

def evaluate_resume(resume_text, target_requirements, api_key=None):
    """Evaluates the resume against the target role requirements using rule-based keyword match and ChromaDB vector search.
    
    Parameters:
    - resume_text: string containing full resume text.
    - target_requirements: dict containing 'hard_skills' and 'tools' from Market Research Agent.
    
    Returns:
    - dict containing:
      - skill_match_score (float, 0.0 - 1.0)
      - resume_opt_score (float, 0.0 - 1.0)
      - matched_skills (list of strings)
      - missing_skills (list of strings)
      - sections_found (list of strings)
    """
    if not resume_text:
        return {
            "skill_match_score": 0.0,
            "resume_opt_score": 0.0,
            "matched_skills": [],
            "missing_skills": target_requirements.get("hard_skills", []) + target_requirements.get("tools", []),
            "sections_found": []
        }

    # 1. Deterministic Section Evaluation (Resume Optimization Score)
    # Check for typical resume sections
    sections = {
        "education": r'\b(education|academic|college|university|qualification)\b',
        "skills": r'\b(skills|technical expertise|technologies|proficiencies|competencies)\b',
        "projects": r'\b(projects|academic projects|work experience|employment|history)\b',
        "certifications": r'\b(certifications|courses|achievements|awards)\b',
        "contact": r'\b(contact|email|phone|mobile|github|linkedin)\b'
    }
    
    sections_found = []
    for section_name, pattern in sections.items():
        if re.search(pattern, resume_text, re.IGNORECASE):
            sections_found.append(section_name)
            
    # Base resume optimization score on found sections + text length check
    resume_opt_score = len(sections_found) / len(sections)
    # Add small bonus for clean formatting indicators (e.g. bullet points or lists)
    if len(re.findall(r'[•\-*]', resume_text)) > 5:
        resume_opt_score = min(1.0, resume_opt_score + 0.1)

    # 2. Setup ChromaDB and Index Resume Chunks
    # Using ephemeral (in-memory) ChromaDB
    chroma_client = chromadb.EphemeralClient()
    emb_fn = MCAEmbeddingFunction(api_key=api_key)
    
    # Create or get collection with a unique name to avoid collisions in the same process
    collection_name = f"resume_chunks_{uuid.uuid4().hex[:8]}"
    collection = chroma_client.create_collection(
        name=collection_name, 
        embedding_function=emb_fn
    )
    
    chunks = chunk_text(resume_text)
    if chunks:
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        collection.add(documents=chunks, ids=ids)
    
    # 3. Match Evaluation: Keywords and ChromaDB vector search
    target_skills = target_requirements.get("hard_skills", []) + target_requirements.get("tools", [])
    matched_skills = []
    missing_skills = []
    
    for skill in target_skills:
        # Check 3.1: Deterministic keyword search (Direct regex)
        # Handle special characters in skills like C++ or .NET
        escaped_skill = re.escape(skill)
        pattern = rf'\b{escaped_skill}\b'
        
        # Fallback regex for skills that might be written differently
        # (e.g., 'scikit-learn' -> 'scikit learn' or 'sklearn')
        if '-' in skill:
            parts = skill.split('-')
            pattern = rf'(\b{re.escape(skill)}\b|\b{" ".join(parts)}\b|\b{"".join(parts)}\b)'
            
        keyword_match = re.search(pattern, resume_text, re.IGNORECASE)
        
        if keyword_match:
            matched_skills.append(skill)
            continue
            
        # Check 3.2: Semantic vector search using ChromaDB
        if chunks:
            # Query the database for the skill
            results = collection.query(
                query_texts=[skill],
                n_results=1
            )
            
            # If we get distances, evaluate similarity
            if results and 'distances' in results and len(results['distances'][0]) > 0:
                distance = results['distances'][0][0]
                
                # In Chroma:
                # For cosine/L2, distance closer to 0 is more similar.
                # Threshold for a match:
                # With our custom TF-IDF, the distance ranges from 0.0 to 2.0 (since L2 norm is 1.0).
                # A distance < 0.8 is generally highly similar.
                # With Gemini embedding, a distance < 0.6 is highly similar.
                threshold = 0.55 if api_key else 0.75
                
                if distance < threshold:
                    matched_skills.append(skill)
                    continue
                    
        # If neither matches, it is a missing skill
        missing_skills.append(skill)

    # 4. Compute overall skill match score
    if target_skills:
        skill_match_score = len(matched_skills) / len(target_skills)
    else:
        skill_match_score = 0.0

    return {
        "skill_match_score": round(skill_match_score, 2),
        "resume_opt_score": round(resume_opt_score, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "sections_found": sections_found
    }
