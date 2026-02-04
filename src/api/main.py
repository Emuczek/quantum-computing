from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sympy as sp
import numpy as np

from src.api.models import QAOARequest, QAOAResponse
from src.core import PyToQ, QAOARunner

app = FastAPI(
    title="QAOA API",
    description="Quantum Approximate Optimization Algorithm as a Service",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "online",
        "message": "QAOA API is running",
        "endpoints": ["/solve-qaoa", "/docs"]
    }


@app.post("/solve-qaoa", response_model=QAOAResponse)
async def solve_qaoa(request: QAOARequest):
    """
    Solve optimization problem using QAOA.
    
    Input example:
```json
    {
        "expression": "5*x[0] + 3*x[1] - 2*x[0]*x[1]",
        "p": 1,
        "maxiter": 50,
        "backend": "simulator",
        "shots": 1024
    }
```
    
    Returns probabilities and optimal parameters.
    """
    try:
        # Step 1: Parse expression
        builder = PyToQ()
        x = builder.create_variable_array('x')  # Creates SymbolicVariableArray
        local_context = {'x': x}
        expr = eval(request.expression, {"__builtins__": {}}, local_context) 
        
        Q, var_map = builder.expression_to_q(expr)
        num_qubits = Q.shape[0]
        
        # Step 3: Convert to Hamiltonian
        H_cost = builder.q_matrix_to_hamiltonian(Q)
        
        # Step 4: Initialize QAOA runner
        runner = QAOARunner(
            backend=request.backend,
            device=request.device
        )
        
        # Step 5: Run optimization
        result = runner.optimize(
            num_qubits=num_qubits,
            cost_hamiltonian=H_cost,
            p=request.p,
            method='COBYLA',
            maxiter=request.maxiter
        )
        
        # Step 6: Sample solution
        counts = runner.sample_solution(
            num_qubits=num_qubits,
            cost_hamiltonian=H_cost,
            gamma=result['optimal_gamma'],
            beta=result['optimal_beta'],
            shots=request.shots,
            p=request.p
        )
        
        # Step 7: Calculate probabilities
        total_shots = sum(counts.values())
        probabilities = {
            bitstring: count / total_shots 
            for bitstring, count in counts.items()
        }
        
        # Step 8: Sort probabilities
        probabilities = dict(
            sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        )
        
        return QAOAResponse(
            success=True,
            optimal_cost=float(result['optimal_cost']),
            optimal_params=result['optimal_params'].tolist(),
            probabilities=probabilities,
            solution_counts=counts,
            num_iterations=result['num_iterations'],
            num_qubits=num_qubits,
            backend=request.backend
        )
    
    except Exception as e:
        return QAOAResponse(
            success=False,
            error=str(e)
        )