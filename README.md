# IT Helpdesk Triage Agent 

A full-stack local IT helpdesk triage app with:
- React frontend for employee and admin workflows
- FastAPI backend for login, ticket creation, admin updates, and dashboard data
- Ollama-powered ticket triage with rule-based fallback
- Local JSON storage for shared ticket state.

## Workflow
- Employee logs in with name, email, and department
- Employee creates a ticket with title and description
- Ticket is analyzed for severity, routing team, rationale, and first-response draft
- Employee can see whether the ticket is resolved or not
- Admin logs in to review analyzed tickets and mark them as `new`, `in_progress`, `waiting_on_user`, `resolved`, or `escalated`

## Structure
- `backend/app/main.py`: FastAPI API
- `backend/app/triage.py`: AI triage + fallback logic
- `backend/app/storage.py`: local ticket persistence
- `frontend/`: React + Vite UI
- `data/tickets.json`: shared ticket data
- 
## Run locally
1. Install Python dependencies:
   ```bash
   ..\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Start Ollama with your model:
   ```bash
   ollama run llama3.2
   ```
4. Start the backend:
   ```bash
   ..\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
   ```
5. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

Frontend runs on `http://localhost:5173`
Backend runs on `http://127.0.0.1:8000`
