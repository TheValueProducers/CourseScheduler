# CourseScheduler

CourseScheduler is a full-stack planning system for Rice University students that combines:

- Degree requirement tracking
- Constraint-based schedule generation (Google OR-Tools CP-SAT)
- Student review collection
- Bayesian-ranked course recommendations

The repository contains a FastAPI backend and a React + Vite frontend.

## What This Program Does

The app provides three user-facing workflows:

1. Main Scheduling Page
- Build a course plan from high school credit through senior year
- Mark classes as planned or attended
- Check requirement progress against one or more selected programs
- Generate an optimized future schedule from the backend solver
- Apply generated classes into semester tables while preserving manually added courses

2. Course Evaluation Input Page
- Search course catalog entries
- Submit structured 1-5 ratings for workload, difficulty, instruction, usefulness, and interest
- Add free-text likes/dislikes
- Store ratings in a PostgreSQL-backed reviews table

3. Course Recommender Ranking Page
- View rankings grouped by D1, D2, D3, Diversity, and LPAP
- Compare courses across multiple metrics
- Use Bayesian-adjusted scores to avoid overrating classes with too few reviews

## Tech Stack

Backend:
- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy
- Alembic
- OR-Tools CP-SAT

Frontend:
- React 18
- Vite 5

Data:
- Rice course catalog JSON in backend/data/rice_course_pages.json
- PostgreSQL for reviews

## Repository Layout

- backend/
  - main.py: FastAPI app factory and router registration
  - scheduler_engine.py: course parsing + scheduling solver + requirement evaluation logic
  - degree_requirement.py: supported degree/minor requirement definitions
  - api/: route modules (schedule, reviews, rankings)
  - services/: business logic layer
  - repositories/: catalog and DB data access
  - db/database.py: SQLAlchemy engine/session and catalog file path
  - models/review.py: review ORM model
  - schemas/: request/response models
  - alembic/: migrations (reviews table migration included)
  - seeds/seed_reviews.py: sample review seeding script
- frontend/
  - src/App.jsx: nav between the 3 pages
  - src/pages/MainSchedulingPage.jsx
  - src/pages/CourseEvaluationInputPage.jsx
  - src/pages/CourseRecommenderRankingPage.jsx

## Architecture Overview

1. Frontend calls backend HTTP APIs
- Frontend is currently configured to call http://localhost:8000

2. Backend services coordinate logic
- API layer validates input via Pydantic schemas
- Service layer orchestrates data loading and solver/ranking execution
- Repository layer reads catalog JSON and review rows

3. Scheduling path
- Catalog is parsed into normalized CourseRecord objects
- Selected degree requirements are loaded from degree_requirement.py
- Solver applies constraints (term offering, prerequisites, requirements, user preferences)
- Response returns semester-by-semester recommendations and requirement status

4. Ranking path
- Reviews are grouped by course and category (D1/D2/D3/diversity/LPAP)
- Metric averages are computed
- Bayesian score is applied using a minimum review threshold
- Results are returned in metric-specific sorted lists

## Prerequisites

- Python 3.12 (recommended)
- Node.js 18+ and npm
- PostgreSQL database reachable from backend configuration

## Local Setup

### 1) Backend setup

From the backend directory:

- Create and activate a virtual environment
  - macOS/Linux:
    - python3 -m venv .venv
    - source .venv/bin/activate
- Install Python dependencies
  - pip install -r requirements.txt
- Run migrations
  - alembic upgrade head
- Start API server
  - ./run.sh
  - or: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Server health check:
- GET http://localhost:8000/health -> {"status":"ok"}

### 2) Frontend setup

From the frontend directory:

- Install dependencies
  - npm install
- Start development server
  - npm run dev

Default frontend dev URL is usually:
- http://localhost:5173

## Database Notes

The current backend DB URL is hardcoded in backend/db/database.py and mirrored in backend/alembic.ini.

For production-quality setup, move this URL to an environment variable, for example DATABASE_URL, and load it in both runtime and Alembic config.

## API Reference

### Health

- GET /health
- Response: status check

### Catalog + Program Metadata

- GET /api/courses
  - Returns list of course summaries: subject, course_number, long_title
- GET /api/programs
  - Returns supported degree/minor options as { value, label }

### Scheduling

- POST /api/schedule
- Request body fields:
  - current_term: Fall | Spring
  - year: Freshman | Sophomore | Junior | Senior
  - completed_courses: ["COMP 140", ...]
  - preferred_courses: ["COMP 321", ...]
  - avoid_courses: ["COMP 422", ...]
  - scheduled_courses: mapping of course -> semester index
  - chosen_degree: list of program keys (example: ["bs_comp"])
  - optimization: balanced | graduate early
- Response includes:
  - status
  - schedule: per-semester recommendations
  - requirements: satisfaction/progress per requirement bucket
  - message (optional)

### Requirement Check

- POST /api/check-requirements
- Request: list of buckets with fields:
  - type: planned | attended
  - classes: list of course codes
  - chosen_degree: list of program keys
- Response: requirement progress rows per bucket

### Reviews

- GET /api/reviews
  - Returns all submitted reviews
- POST /api/reviews
  - Accepts 1-5 integer ratings + free-text comments + subject/course_number
  - Returns created review row with id

### Rankings

- GET /api/rankings
- GET /api/rankings/by-group
- Returns grouped rankings for:
  - d1
  - d2
  - d3
  - diversity
  - lpap

Each group contains metric lists (workload, overall_diff, instructor, usefulness, etc.) sorted by Bayesian score descending.

## How Scheduling Works (High-Level)

The scheduler uses CP-SAT constraints and catalog parsing rules:

- Normalizes course codes to SUBJECT NNN format
- Parses offered terms from catalog rows
- Parses prerequisites into expression trees with AND/OR nodes
- Tracks completed, already scheduled, preferred, and avoided courses
- Applies selected degree/minor requirement constraints
- Optimizes based on selected mode

The solver output is transformed into semester labels:
- Freshman Fall -> Senior Spring

## How Ranking Works (High-Level)

For each course in a group:

- Compute raw mean score per metric from submitted reviews
- Compute global mean score per metric across all reviews
- Compute Bayesian-adjusted score:
  - score = (v/(v+m))*r + (m/(v+m))*c
  - v: number of reviews for the course
  - m: minimum review threshold (currently 10)
  - r: course mean for the metric
  - c: global mean for the metric

This reduces volatility for courses with few reviews.

## Seeding Sample Reviews

A helper script exists at backend/seeds/seed_reviews.py.

Run from backend directory:
- python seeds/seed_reviews.py

Use this to populate initial ranking data quickly.

## Testing Status

There is a backend/tests directory placeholder, but no automated test suite is currently implemented.

Recommended additions:
- API endpoint tests (FastAPI TestClient)
- Solver unit tests for prerequisite/term/requirement edge cases
- Ranking tests for Bayesian score correctness

## Troubleshooting

1. OR-Tools / pandas / numpy import issues
- This project pins pandas and numpy versions in requirements.txt for compatibility.
- Reinstalling in a clean virtual environment usually fixes binary mismatch errors.

2. Frontend cannot reach backend
- Ensure backend is running on port 8000
- Ensure frontend API URL constant points to correct backend URL
- Confirm CORS origins include your frontend origin

3. Database errors on review endpoints
- Verify DATABASE URL credentials and host
- Run alembic upgrade head to ensure reviews table exists

4. No ranking results
- Submit or seed reviews first
- Rankings only show courses that have review data

## Deployment Notes

Backend:
- Dockerfile provided in backend/
- Default container command runs uvicorn on port 8080

Frontend:
- Standard Vite build pipeline (npm run build)

You can host frontend and backend separately, as long as:
- Backend CORS allow_origins includes frontend origin
- Frontend API URL points to deployed backend domain

## Suggested Next Improvements

- Move secrets and DB URL to environment variables
- Add automated test coverage for solver and API
- Add authentication/user identities for reviews
- Add pagination/filtering for reviews and rankings
- Add OpenAPI examples for request bodies

## License

No license file is currently present in this repository. Add one if you plan to distribute this project publicly.
