from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Literal

class ParseLatexRequest(BaseModel):
    """
    Request body for /api/parse-latex endpoint.
    
    Example:
        {
            "latex": "\\min \\sum_{i=0}^{2} w_i x_i"
        }
    """
    latex: str = Field(description="LaTeX expression to parse")
    
    @field_validator('latex')
    @classmethod
    def latex_not_empty(cls, v: str) -> str:
        """Validate that LaTeX string is not empty."""
        if not v or not v.strip():
            raise ValueError("LaTeX expression cannot be empty")
        return v.strip()


class ParseLatexResponse(BaseModel):
    """Response from /api/parse-latex endpoint."""
    success: bool
    parsed_expression: Optional[str] = None
    variables: Optional[List[str]] = None
    parameters: Optional[List[str]] = None
    error: Optional[str] = None


class GenerateQuboRequest(BaseModel):
    """
    Request body for /api/generate-qubo endpoint.
    
    Example:
        {
            "expression": "5*x[0] + 3*x[1] - 2*x[0]*x[1]",
            "num_vars": 2
        }
    """
    expression: str = Field(description="Python/SymPy expression with variables")
    num_vars: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of variables (auto-detected if not provided)"
    )


class HamiltonianData(BaseModel):
    """
    Represents a quantum Hamiltonian in Pauli basis.
    
    Example:
        {
            "paulis": ["ZI", "IZ", "ZZ"],
            "coeffs": [-2.0, -1.0, -0.5]
        }
    """
    paulis: List[str] = Field(description="Pauli strings (e.g., 'ZI', 'IZ', 'ZZ')")
    coeffs: List[float] = Field(description="Coefficients for each Pauli term")


class GenerateQuboResponse(BaseModel):
    """Response from /api/generate-qubo endpoint."""
    success: bool
    Q_matrix: Optional[List[List[float]]] = None
    hamiltonian: Optional[HamiltonianData] = None
    num_qubits: Optional[int] = None
    variable_mapping: Optional[Dict[str, str]] = None
    error: Optional[str] = None


class RunQaoaRequest(BaseModel):
    """
    Request body for /api/run-qaoa endpoint.
    
    Example:
        {
            "num_qubits": 2,
            "hamiltonian": {
                "paulis": ["ZI", "IZ", "ZZ"],
                "coeffs": [-2.0, -1.0, -0.5]
            },
            "p": 1,
            "maxiter": 50,
            "backend": "simulator"
        }
    """
    num_qubits: int = Field(ge=1, le=20, description="Number of qubits")
    hamiltonian: HamiltonianData = Field(description="Cost Hamiltonian in Pauli basis")
    p: int = Field(default=1, ge=1, le=5, description="QAOA depth")
    maxiter: int = Field(default=50, ge=10, le=200, description="Max optimization iterations")
    backend: Literal["simulator", "ibm"] = Field(default="simulator")
    device: Optional[str] = Field(default=None, description="IBM device name")
    shots: int = Field(default=1024, ge=100, le=10000, description="Measurement shots")
    optimizer: str = Field(default="COBYLA", description="Classical optimizer")


class RunQaoaResponse(BaseModel):
    """Response from /api/run-qaoa endpoint."""
    success: bool
    optimal_cost: Optional[float] = None
    optimal_params: Optional[List[float]] = None
    optimal_gamma: Optional[List[float]] = None
    optimal_beta: Optional[List[float]] = None
    solution_counts: Optional[Dict[str, int]] = None
    num_iterations: Optional[int] = None
    backend: Optional[str] = None
    device: Optional[str] = None
    quantum_time_seconds: Optional[float] = None
    convergence_history: Optional[List[Dict]] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""
    status: str
    message: str
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = False
    error: str
    detail: Optional[str] = None