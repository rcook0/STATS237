# Stats237 v0.7 — API

The API is intended to be **callable and reproducible**: every response includes a `provenance` envelope with version + runtime metadata + request hash + effective seed.

## Start the server

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e stats237_quantlib
python -m pip install -r requirements.txt

uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Interactive docs:
- http://127.0.0.1:8000/docs

## Response envelope

All endpoints return:

```json
{
  "provenance": { "request_id": "...", "request_hash": "...", "package_version": "0.7.0", "seed_effective": 123, "received_at": "...", "runtime": {"python": "...", "numpy": "..."} },
  "result": { "...": "..." }
}
```

## Endpoints

### Meta
- `GET /health`
- `GET /meta`

### Black–Scholes
- `POST /price/black_scholes` (call or put)
- `POST /greeks/black_scholes`
- `POST /implied_vol`

### Binomial (CRR)
- `POST /price/binomial` (European/American, call/put)

### Monte Carlo
- `POST /mc/asian/arithmetic_call` (antithetic + geometric control variate)
- `POST /mc/basket/call` (antithetic/LHS + geometric control variate)

## Example: Black–Scholes call

```bash
curl -s http://127.0.0.1:8000/price/black_scholes \
  -H "Content-Type: application/json" \
  -d '{"S0":100,"K":100,"r":0.02,"T":1.0,"sigma":0.2,"is_call":true}'
```

## Example: Basket call MC (variance reduced)

```bash
curl -s http://127.0.0.1:8000/mc/basket/call \
  -H "Content-Type: application/json" \
  -d '{
    "S0":[100,95],
    "w":[0.5,0.5],
    "K":100,
    "r":0.02,
    "T":1.0,
    "vol":[0.2,0.25],
    "corr":[[1,0.4],[0.4,1]],
    "n_paths":20000,
    "seed":123,
    "antithetic":true,
    "lhs":false,
    "use_control_variate":true,
    "alpha":0.05
  }'
```
