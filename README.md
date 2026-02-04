# QAOA Backend API

REST API for Quantum Approximate Optimization Algorithm (QAOA) - a quantum approximation optimization algorithm.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-green.svg)](https://fastapi.tiangolo.com/)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.2.3-purple.svg)](https://qiskit.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## About

This system enables solving combinatorial optimization problems using the QAOA algorithm through a REST API interface. It converts mathematical expressions into quantum format, performs optimization, and returns the probability distribution of solutions.

**Features:**
- Automatic conversion of expressions to QUBO format
- Construction and optimization of QAOA quantum circuits
- Support for local simulator and IBM Quantum hardware
- REST API with automatic documentation (OpenAPI)
- Docker containerization

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/Emuczek/quantum-computing.git
cd quantum-computing
docker compose up --build
```

API available at: http://localhost:8000

### Local Installation

```bash
git clone https://github.com/Emuczek/quantum-computing.git
cd quantum-computing
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Usage

### Basic Example

```bash
curl -X POST http://localhost:8000/solve-qaoa \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "5*x[0] + 3*x[1] - 2*x[0]*x[1]",
    "p": 1,
    "maxiter": 50,
    "backend": "simulator",
    "shots": 1024
  }'
```

### Response

```json
{
  "success": true,
  "optimal_cost": -2.6747,
  "optimal_params": [2.674, 2.370],
  "probabilities": {
    "00": 0.862,
    "10": 0.073,
    "11": 0.040,
    "01": 0.025
  },
  "num_qubits": 2,
  "backend": "simulator"
}
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/solve-qaoa",
    json={
        "expression": "x[0]*x[1] + x[1]*x[2]",
        "p": 2,
        "maxiter": 100,
        "backend": "simulator"
    }
)

result = response.json()
print(f"Optimal cost: {result['optimal_cost']}")
```

## API Documentation

After starting the server:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoint

**POST /solve-qaoa**

| Parameter  | Type   | Default   | Description                    |
|------------|--------|-----------|--------------------------------|
| expression | string | required  | Python expression (e.g., `x[0] + x[1]`) |
| p          | int    | 1         | QAOA depth (1-5)               |
| maxiter    | int    | 50        | Maximum iterations             |
| backend    | string | simulator | "simulator" or "ibm"           |
| shots      | int    | 1024      | Number of measurements         |

## IBM Quantum Configuration

To use real IBM hardware (needed to run only once):

```bash
# 1. Copy the template
cp src/core/save_ibm_credentials.py src/core/save_ibm_credentials_local.py

# 2. Edit the local file and enter your token from https://quantum.ibm.com/account
# IBM_TOKEN = "your_token"
# CRN = "your_crn"

# 3. Save credentials
python src/core/save_ibm_credentials_local.py
```