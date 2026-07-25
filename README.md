# AstraX AI

> Research-Grade Asteroid Detection & Astronomical Image Analysis Platform

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![Next.js](https://img.shields.io/badge/next.js-16-black)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-teal)

AstraX AI is a professional astronomical image analysis platform that helps researchers detect moving celestial candidates in FITS datasets. It combines advanced image processing algorithms with an intuitive observatory-style interface and AI-powered explanations.

## ✨ Features

- **FITS Dataset Management** — Import, index, and browse FITS files with automatic header extraction
- **Advanced Image Processing** — Calibration, noise reduction, enhancement, and image registration
- **Multi-Algorithm Detection** — DAOStarFinder, IRAFStarFinder, optical flow, frame differencing
- **Motion Analysis** — Lucas-Kanade, Farneback optical flow, trajectory fitting
- **False Positive Filtering** — Cosmic ray, hot pixel, satellite streak, and artifact rejection
- **Confidence Ranking** — Multi-factor scoring with motion consistency, SNR, and persistence
- **Blink Comparator** — Rapid frame alternation for visual detection
- **AI Assistant** — LLM-powered explanations and report generation (Gemini, OpenAI, Anthropic, OpenRouter)
- **Export Center** — CSV, JSON, PDF reports, annotated images, session archives
- **Observatory UI** — Deep space aesthetic with glassmorphism, neon accents, and smooth animations

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **npm**

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd astrax-ai

# Copy environment config
cp .env.example .env

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
astrax-ai/
├── frontend/          # Next.js 16 + TypeScript + Tailwind CSS
├── backend/           # FastAPI + SQLAlchemy + Celery
├── engine/            # Python astronomy package (astropy, photutils, OpenCV)
├── ai_service/        # LLM provider abstraction layer
└── docker-compose.yml
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Framer Motion, Zustand, Recharts |
| Backend | FastAPI, SQLAlchemy (async), Pydantic v2, Celery |
| Engine | astropy, photutils, OpenCV, scikit-image, NumPy, SciPy |
| Database | SQLite (local) / PostgreSQL (production) |
| AI | Gemini, OpenAI, Anthropic, OpenRouter |
| Infrastructure | Docker, Redis, Makefile |

## 📡 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 🔬 Detection Pipeline

1. **Import Dataset** → Scan and index FITS files
2. **Calibrate Frames** → Flat field, dark frame, bias correction
3. **Align Images** → Star-based registration
4. **Detect Sources** → DAOStarFinder / IRAFStarFinder
5. **Analyze Motion** → Optical flow, frame differencing
6. **Filter Artifacts** → Cosmic rays, hot pixels, streaks
7. **Rank Candidates** → Multi-factor confidence scoring
8. **Human Review** → Confirm, reject, or flag candidates
9. **Export Report** → PDF, CSV, JSON, annotated images

## ⚙️ Configuration

All settings are configured via environment variables (prefix: `ASTRAX_`). See `.env.example` for full documentation.

### AI Assistant Setup

```bash
# In your .env file:
ASTRAX_LLM_PROVIDER=gemini          # or openai, anthropic, openrouter
ASTRAX_LLM_MODEL=gemini-2.0-flash
ASTRAX_LLM_API_KEY=your-api-key
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
