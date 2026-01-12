from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
import numpy as np


class QAOACircuit:
    """
    Builds QAOA circuits for a given cost Hamiltonian.
    
    Parameters:
        num_qubits: Number of qubits
        cost_hamiltonian: SparsePauliOp representing the cost function
        p: Number of QAOA layers (depth)
    """
    
    def __init__(self, num_qubits: int, cost_hamiltonian: SparsePauliOp, p: int = 1):
        self.num_qubits = num_qubits
        self.cost_hamiltonian = cost_hamiltonian
        self.p = p
        
        self.mixer_hamiltonian = SparsePauliOp.from_list(
            [(("I" * i + "X" + "I" * (num_qubits - i - 1)), 1.0) 
             for i in range(num_qubits)]
        )
    
    def build_circuit(self, gamma: np.ndarray, beta: np.ndarray) -> QuantumCircuit:
        """
        Build QAOA circuit with given parameters.
        
        Args:
            gamma: Array of γ parameters (length p) for cost Hamiltonian
            beta: Array of β parameters (length p) for mixer Hamiltonian
            
        Returns:
            QuantumCircuit ready for execution
        """
        if len(gamma) != self.p or len(beta) != self.p:
            raise ValueError(f"Expected {self.p} parameters, got γ={len(gamma)}, β={len(beta)}")
        
        qc = QuantumCircuit(self.num_qubits)
        
        qc.h(range(self.num_qubits))
        
        for layer in range(self.p):
            self._apply_hamiltonian(qc, self.cost_hamiltonian, gamma[layer])
            self._apply_hamiltonian(qc, self.mixer_hamiltonian, beta[layer])
        
        return qc
    
    def _apply_hamiltonian(self, qc: QuantumCircuit, hamiltonian: SparsePauliOp, angle: float):
        """Apply Hamiltonian evolution for QUBO problems (Z, ZZ, X terms only)."""
        
        print(f"\n--- Applying Hamiltonian (angle={angle}) ---")
        print(f"Hamiltonian: {hamiltonian}")
        
        for pauli_str, coeff in hamiltonian.to_list():
            theta = 2 * angle * coeff.real
        
            z_qubits = [i for i, p in enumerate(pauli_str) if p == 'Z']
            x_qubits = [i for i, p in enumerate(pauli_str) if p == 'X']
            
            if len(z_qubits) == 1:
                qc.rz(theta, z_qubits[0])
            elif len(z_qubits) == 2:
                qc.rzz(theta, z_qubits[0], z_qubits[1])
            if len(x_qubits) == 1:
                qc.rx(theta, x_qubits[0])