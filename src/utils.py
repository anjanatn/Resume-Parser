import re

# Comprehensive Skills Taxonomy with canonical name mapping
SKILLS_TAXONOMY = {
    # Programming Languages
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c++": "C++",
    "c#": "C#",
    "go": "Go",
    "golang": "Go",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "dart": "Dart",
    "rust": "Rust",
    "sql": "SQL",
    "bash": "Bash",
    "shell": "Bash",

    # Web & Frontend Frameworks
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue.js",
    "angular": "Angular",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "tailwind": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "sass": "Sass",
    "redux": "Redux",

    # Backend & API Frameworks
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "spring": "Spring Boot",
    "spring boot": "Spring Boot",
    "spring cloud": "Spring Cloud",
    "express": "Express.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "graphql": "GraphQL",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "restful": "REST APIs",
    "microservices": "Microservices",

    # AI, ML & Data Science
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "huggingface": "HuggingFace",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "llm": "LLMs",
    "llms": "LLMs",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "tableau": "Tableau",
    "powerbi": "PowerBI",
    "power bi": "PowerBI",
    "statistics": "Statistics",

    # Cloud, DevOps & Infrastructure
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "ci/cd": "CI/CD",
    "redis": "Redis",
    "kafka": "Kafka",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "linux": "Linux",

    # Databases
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "oracle": "Oracle DB",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "sqlite": "SQLite",

    # Cybersecurity & Tools
    "cybersecurity": "Cybersecurity",
    "wireshark": "Wireshark",
    "siem": "SIEM",
    "penetration testing": "Penetration Testing",
    "owasp": "OWASP",
    "git": "Git",
    "figma": "Figma",
    "flutter": "Flutter",
    "firebase": "Firebase",

    # Management & Agile
    "agile": "Agile",
    "scrum": "Scrum",
    "jira": "JIRA",
    "product strategy": "Product Strategy",
    "roadmap planning": "Roadmap Planning",
    "user research": "User Research",
    "a/b testing": "A/B Testing"
}

# Regex patterns for contact information
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
LINKEDIN_REGEX = r'(?:linkedin\.com\/in\/[a-zA-Z0-9_-]+)'
GITHUB_REGEX = r'(?:github\.com\/[a-zA-Z0-9_-]+)'

DEGREE_PATTERNS = [
    (r'(?i)\bph\.?d\.?\b|\bdoctor of philosophy\b', "PhD", 5),
    (r'(?i)\bmaster\'?s?\b|\bm\.?s\.?\b|\bm\.?b\.?a\.?\b|\bmaster of science\b|\bmaster of business\b', "Master's", 4),
    (r'(?i)\bbachelor\'?s?\b|\bb\.?s\.?\b|\bb\.?a\.?\b|\bb\.?tech\b|\bbachelor of science\b|\bbachelor of arts\b', "Bachelor's", 3),
    (r'(?i)\bassociate\'?s?\b|\ba\.?s\.?\b', "Associate's", 2)
]

def clean_text(text):
    """Normalize text whitespace and characters."""
    if not text:
        return ""
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_email(text):
    match = re.search(EMAIL_REGEX, text)
    return match.group(0) if match else None

def extract_phone(text):
    match = re.search(PHONE_REGEX, text)
    return match.group(0) if match else None

def extract_linkedin(text):
    match = re.search(LINKEDIN_REGEX, text)
    return match.group(0) if match else None

def extract_github(text):
    match = re.search(GITHUB_REGEX, text)
    return match.group(0) if match else None
