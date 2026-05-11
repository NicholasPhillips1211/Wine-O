# Backend (FastAPI)

This folder contains the FastAPI microservices. Start by creating a virtual environment and installing dependencies listed in `requirements.txt`.

Development:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
