# AstraX AI

> Research-Grade Asteroid Detection & Astronomical Image Analysis Platform

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![Next.js](https://img.shields.io/badge/next.js-16-black)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-teal)

🌐 **Live Demo**: [astrax.vercel.app](https://astrax.vercel.app)

AstraX AI is a professional astronomical image analysis platform that helps researchers detect moving celestial candidates in FITS datasets, images, and tabular data. It combines a **5-model ML ensemble** with an intuitive observatory-style interface and AI-powered explanations.

## ✨ Features

- **FITS Dataset Management** — Import, index, and browse FITS files with automatic header extraction
- **Advanced Image Processing** — Calibration, noise reduction, enhancement, and image registration
- **5-Model ML Ensemble Detection** — Consensus voting across IsolationForest, LocalOutlierFactor, EllipticEnvelope, SGDOneClassSVM, and Z-Score statistical outlier detection
- **Astronomical Source Detection** — DAOStarFinder, IRAFStarFinder, adaptive multi-threshold detection
- **Computer Vision Pipeline** — OpenCV HOG descriptors, adaptive thresholding, contour analysis
- **Motion Analysis** — Lucas-Kanade & Farneback optical flow, frame differencing, trajectory fitting
- **False Positive Filtering** — DBSCAN spatial clustering, cosmic ray, hot pixel, satellite streak, and saturation artifact rejection
- **Confidence Ranking** — Multi-factor scoring with motion consistency, SNR, persistence, and ensemble agreement
- **Real-Time Pipeline Monitoring** — Live progress tracking with detailed log output during detection
- **Blink Comparator** — Rapid frame alternation for visual detection
- **Multi-LLM AI Assistant** — Classifications, explanations, and analysis powered by **DeepSeek, Grok, Gemini, OpenAI, and OpenRouter**
- **Export Center** — CSV, JSON, PDF reports, annotated images, session archives
- **Mobile-First UI** — Fully responsive Vercel-inspired dark theme design

## 🧠 Detection Models

### Tabular Data (CSV/JSON) — 5-Model Ensemble
| Model | Type | Strength |
|---|---|---|
| **IsolationForest** | Tree-based | Isolates anomalies by random partitioning |
| **LocalOutlierFactor** | Density-based | Finds locally anomalous points in feature space |
| **EllipticEnvelope** | Distribution-based | Detects outliers from Gaussian distribution |
| **SGDOneClassSVM** | Boundary-based | Learns decision boundary around normal data |
| **Z-Score Outlier** | Statistical | Classical sigma-clipping across all features |

A row is flagged only when **≥2 out of 5** models agree it is anomalous. Confidence = (agreeing models / total models).

### Astronomical Images (FITS)
- **DAOStarFinder** — Point source detection
- **IRAFStarFinder** — Alternative photometric detection
- **Adaptive Multi-Threshold** — Runs at σ = 3, 5, 7, 10 and merges
- **Segmentation + Deblending** — For extended/blended sources

### Standard Images (JPG/PNG)
- **OpenCV Adaptive Thresholding** — Local anomaly detection
- **HOG Descriptor Analysis** — Structural feature extraction
- **Contour Analysis** — Shape-based classification

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **npm**

### Installation

```bash
# Clone the repository
git clone https://github.com/nirmalya-ghosh/ASTRA-X.git
cd ASTRA-X

# Copy environment config
cp .env.example backend/.env

# Install frontend dependencies
cd frontend && npm install && cd ..

# Install backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Install the engine as a package
cd engine && pip install -e ".[all]" && cd ..
```

### Running

```bash
# Terminal 1: Start the backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Docker

```bash
docker compose up --build
```

## 🏗️ Architecture

```
ASTRA-X/
├── frontend/          # Next.js 16 + TypeScript + Tailwind CSS
├── backend/           # FastAPI + SQLAlchemy (async)
├── engine/            # Python astronomy & ML package
└── docker-compose.yml
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy (async), Pydantic v2 |
| ML Engine | scikit-learn (IsolationForest, LOF, EllipticEnvelope, SGDOneClassSVM), astropy, photutils, OpenCV |
| Database | SQLite (local) / PostgreSQL (production) |
| AI | DeepSeek, Grok, Gemini, OpenAI, OpenRouter |
| Deploy | Vercel (frontend) + Render (backend) |

## 📡 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 🔬 Detection Pipeline

1. **Upload Dataset** → Drag & drop FITS, CSV, JSON, or images
2. **Index Files** → Background file scanning and metadata extraction
3. **Run Ensemble Detection** → 5 ML models vote on every data point
4. **Consensus Filtering** → Only anomalies with ≥2 model agreement pass
5. **Confidence Scoring** → Score = (agreeing models / total models)
6. **Real-Time Progress** → Frontend polls backend task status every 2 seconds
7. **Results Dashboard** → Confidence bars, detection method badges, summary stats
8. **AI Classification** → Use DeepSeek/GPT-4o/Grok to classify candidates
9. **Export Report** → PDF, CSV, JSON, annotated images

## ⚙️ Configuration

All settings are configured via environment variables (prefix: `ASTRAX_`). See `.env.example` for full documentation.

### AI Assistant Setup

```bash
# In your backend/.env file:
ASTRAX_LLM_PROVIDER=deepseek
ASTRAX_LLM_DEEPSEEK_API_KEY=your-api-key
ASTRAX_LLM_OPENAI_API_KEY=your-api-key
ASTRAX_LLM_GEMINI_API_KEY=your-api-key
ASTRAX_LLM_GROK_API_KEY=your-api-key
```

## 🧪 Testing

```bash
# Engine tests
cd engine && python -m pytest tests/ -v

# Backend tests
cd backend && python -m pytest tests/ -v

# Frontend lint
cd frontend && npm run lint
```

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

**Note**: AstraX AI assists human review of astronomical data. It does not replace scientific validation. All detections should be verified by qualified researchers before publication.
