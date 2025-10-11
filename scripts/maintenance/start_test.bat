@echo off
cd app\backend
python -m uvicorn main:app --host 0.0.0.0 --port 9393
pause

