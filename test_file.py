import requests

response = requests.post(
    "http://localhost:8000/solve-qaoa",
    json={
        "expression": "5*x[0] + 3*x[1] - 2*x[0]*x[1]",
        "p": 1,
        "maxiter": 30,
        "backend": "simulator",
        "shots": 1024
    }
)

print(response.json())