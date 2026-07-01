"""
config/jd_config.py

All JD-specific knowledge lives here, separated from the generic scoring
engine in src/. This is intentional: the JD changes, the engine shouldn't
have to.

Every list below was built by reading job_description.docx closely AND by
inspecting the actual vocabulary used in candidates.jsonl (skills, titles,
industries, companies) so the keyword matching works against what the data
actually contains rather than a guessed-at vocabulary.
"""

# ---------------------------------------------------------------------------
# Role title classification
# ---------------------------------------------------------------------------
# Built from the 44 distinct `current_title` values observed in the dataset.

AI_ML_CORE_TITLES = {
    "ai specialist", "ml engineer", "ai research engineer", "junior ml engineer",
    "data scientist", "computer vision engineer", "senior software engineer (ml)",
    "recommendation systems engineer", "applied ml engineer", "senior data scientist",
    "nlp engineer", "ai engineer", "search engineer", "machine learning engineer",
    "senior ai engineer", "senior nlp engineer", "senior machine learning engineer",
}

ADJACENT_TECH_TITLES = {
    "software engineer", "senior software engineer", "backend engineer",
    "data engineer", "senior data engineer", "analytics engineer", "data analyst",
    "full stack developer", "devops engineer", "frontend engineer", "cloud engineer",
    "qa engineer", "java developer", ".net developer", "mobile developer",
}

NON_TECH_TITLES = {
    "hr manager", "mechanical engineer", "content writer", "accountant",
    "business analyst", "sales executive", "civil engineer", "customer support",
    "project manager", "operations manager", "graphic designer", "marketing manager",
}

# ---------------------------------------------------------------------------
# Skill vocabulary (from the 129 distinct skill names seen in candidates.jsonl)
# ---------------------------------------------------------------------------

# "Production experience with embeddings-based retrieval systems" (JD: must-have)
RETRIEVAL_EMBEDDING_SKILLS = {
    "embeddings", "sentence transformers", "vector search", "semantic search",
    "rag", "information retrieval", "information retrieval systems", "bm25",
    "haystack", "llamaindex", "search & discovery", "search backend",
    "text encoders", "vector representations", "content matching",
    "ranking systems",
}

# "Production experience with vector databases or hybrid search infra" (JD: must-have)
VECTOR_DB_SKILLS = {
    "pinecone", "faiss", "qdrant", "weaviate", "milvus", "elasticsearch",
    "opensearch", "pgvector",
}

# "Hands-on experience designing evaluation frameworks for ranking systems" (must-have)
EVAL_FRAMEWORK_SKILLS = {
    "learning to rank", "mlops", "mlflow", "weights & biases",
    "feature engineering", "statistical modeling",
}

# "Strong Python" (must-have) -- core ML/production stack signal
PYTHON_ML_STACK_SKILLS = {
    "python", "pytorch", "tensorflow", "scikit-learn",
}

# Nice-to-haves explicitly named in the JD
LLM_FINETUNE_SKILLS = {"lora", "qlora", "peft", "fine-tuning llms"}
LEARNING_TO_RANK_SKILLS = {"learning to rank"}
NLP_LLM_ADJACENT_SKILLS = {
    "nlp", "natural language processing", "llms", "hugging face transformers",
    "prompt engineering", "langchain", "recommendation systems",
}

# Narrow specializations the JD explicitly says require NLP/IR overlap to count
CV_SPEECH_ROBOTICS_SKILLS = {
    "computer vision", "image classification", "object detection", "yolo",
    "opencv", "cnn", "gans", "diffusion models", "speech recognition", "asr",
    "tts",
}

ALL_AI_CORE_SKILLS = (
    RETRIEVAL_EMBEDDING_SKILLS | VECTOR_DB_SKILLS | EVAL_FRAMEWORK_SKILLS
    | PYTHON_ML_STACK_SKILLS | LLM_FINETUNE_SKILLS | NLP_LLM_ADJACENT_SKILLS
    | CV_SPEECH_ROBOTICS_SKILLS
    | {"deep learning", "machine learning", "data science", "time series",
       "forecasting", "reinforcement learning", "feature engineering"}
)

# ---------------------------------------------------------------------------
# Company / industry classification
# ---------------------------------------------------------------------------

# JD: "people who have only worked at consulting firms ... in their entire career"
CONSULTING_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "mindtree", "mphasis", "tech mahindra",
}

# Industry tags in the dataset that directly signal AI-native / AI-relevant work
AI_NATIVE_INDUSTRIES = {
    "ai/ml", "ai services", "conversational ai", "voice ai", "healthtech ai",
}

# HR-tech / recruiting / marketplace adjacency (JD: nice-to-have)
HR_MARKETPLACE_INDUSTRIES = {"hr tech", "saas", "e-commerce", "fintech"}
HR_MARKETPLACE_COMPANIES = {
    "haptik", "yellow.ai", "verloop.io", "saarthi.ai", "krutrim", "sarvam ai",
    "observe.ai", "rephrase.ai", "mad street den", "niramai", "genpact ai",
    "aganitha",
}

# Companies in the dataset that are clearly product/tech companies (positive
# "product company, not pure services" signal -- used only as a mild tie-break,
# never as a hard requirement, since global big-tech culture-fit concerns in
# the JD are not something we can verify from structured data).
KNOWN_PRODUCT_COMPANIES = {
    "google", "meta", "microsoft", "amazon", "apple", "netflix", "linkedin",
    "salesforce", "adobe", "uber", "flipkart", "swiggy", "zomato", "ola",
    "paytm", "phonepe", "razorpay", "cred", "meesho", "nykaa", "dream11",
    "inmobi", "unacademy", "vedantu", "byju's", "upgrad", "policybazaar",
    "pharmeasy", "glance", "zoho", "freshworks",
} | HR_MARKETPLACE_COMPANIES

# ---------------------------------------------------------------------------
# Location tiers (JD: Pune/Noida preferred, Hyderabad/Pune/Mumbai/Delhi NCR
# explicitly welcome, no visa sponsorship outside India)
# ---------------------------------------------------------------------------

LOCATION_TIER_1 = {"pune, maharashtra", "noida, uttar pradesh"}
LOCATION_TIER_2 = {
    "hyderabad, telangana", "mumbai, maharashtra", "delhi, delhi",
    "gurgaon, haryana", "bangalore, karnataka",
}
# all other India locations fall through to a lower default score

# ---------------------------------------------------------------------------
# Experience band
# ---------------------------------------------------------------------------
TARGET_YOE_MIN = 5
TARGET_YOE_MAX = 9
# JD wants ~4-5 years specifically *in applied ML/AI roles*
TARGET_ML_YOE = 4.5

# ---------------------------------------------------------------------------
# Scoring weights (composite, pre-disqualifier-multiplier; sums to 1.0)
# ---------------------------------------------------------------------------
WEIGHTS = {
    "title_role_fit": 0.32,      # career-weighted AI/ML role relevance
    "must_have_skills": 0.23,    # retrieval/embeddings/vectordb/eval/python
    "experience_band": 0.08,     # 5-9 yrs total, soft curve
    "nice_to_have": 0.07,        # fine-tuning, LTR, HR-tech, distributed sys
    "location_fit": 0.09,        # Pune/Noida/Tier-2/elsewhere/intl
    "notice_period": 0.05,       # <=30d preferred
    "availability": 0.16,        # behavioral / Redrob engagement signals
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
