# Deployment (Step 5)

Local Docker
------------

```bash
docker compose up --build
```

Then open:

- http://localhost:8000/docs

Notes
-----

- The image installs `requirements.txt` then `pip install -e stats237_quantlib`.
- For reproducible deployments, pin versions in `requirements.txt` / `pyproject.toml`.
