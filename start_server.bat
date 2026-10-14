@echo off
cd D:\projects\AutomiqueRAG
\.venv\Scripts\python.exe -c "import uvicorn; uvicorn.run('src.main:app', host='127.0.0.1', port=8000, log_level='info')"