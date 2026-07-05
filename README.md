# AI-Powered Internship Recommendation Engine

An intelligent match-making portal built under the guidelines of the **Prime Minister's Internship Scheme**, designed to automatically parse student resumes, analyze skill gaps, and match candidates with the most relevant internship opportunities.

---

## Key Features

### 1. AI-First Resume Parser
* **Multi-stage Extraction**: Parses PDF resumes using a robust pipeline of `pdfplumber`, `PyMuPDF`, and `pypdf`.
* **Gemini AI Integration**: Extracts structured profile data (JSON) directly from resume text using Gemini models with strict validation and no hallucinations.
* **Deterministic Local Fallback**: Safely falls back to an advanced regex-based parser if the API key is not configured.

### 2. Smart Autofill & Preview
* **Side-by-Side Verification**: Displays a premium comparison modal showing **Current Profile Value ➔ Detected Value** for each field.
* **Confidence Scoring**: Assigns a confidence value to every parsed field; automatically ticks high-confidence fields ($\ge 70\%$) and alerts users on low-confidence ones.
* **Smart Merging**: Intelligently updates skills (replaces old ones with normalized new ones) and merges interests instead of blindly overwriting.

### 3. Hybrid ML Recommendation Engine
* **Semantic Analysis**: Computes TF-IDF vector embeddings and Cosine Similarity scores matching profile keywords against internship descriptions.
* **Structured Eligibility Matching**: Combines semantic matching with strict filters for academic branch, degree, CGPA, location preferences, and target industry.
* **Explainable AI (XAI)**: Displays a clear, percentage-based score breakdown explaining how the match percentage (e.g. 83%) was calculated.

### 4. Interactive Student & Admin Portals
* **Student Portfolio**: View, track, and apply for matched opportunities, save bookmarks, and follow custom week-by-week learning roadmaps for missing skills.
* **Admin Dashboard**: System-wide analytics on student registration, skill demands, and work-mode distributions utilizing interactive Chart.js visualization.

---

## Tech Stack

* **Backend**: Python, Flask, Flask-SQLAlchemy (SQLite)
* **Frontend**: HTML5, Vanilla CSS3 (Slate-Ocean Premium Theme), JavaScript (SPA architecture)
* **AI / ML**: Google Gemini API (`google-genai`), Scikit-Learn (`TfidfVectorizer`), NumPy
* **PDF Extraction**: `pdfplumber`, `pypdf`, `pymupdf`

---

