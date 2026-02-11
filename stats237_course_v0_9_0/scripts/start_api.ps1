param(
  [string]$Host = "127.0.0.1",
  [int]$Port = 8000
)

python -m pip install -r requirements.txt
uvicorn api.app:app --host $Host --port $Port
