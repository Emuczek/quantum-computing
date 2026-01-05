import sympy as sp
import numpy as np 
from typing import Dict, Tuple, Any, Callable
import re
from qiskit.quantum_info import SparsePauliOp

class SymbolicVariableArray:
    """
    A dict-like object that creates SymPy symbols on-the-fly when accessed.
    
    Usage:
        x = SymbolicVariableArray('x')
        expr = x[0,1,2]  # Creates Symbol('x_0_1_2')
    """
    
    def __init__(self, name: str):
        self.name = name
        self._cache = {} 
    
    def __getitem__(self, key):

        if not isinstance(key, tuple):
            key = (key,)
        
        if key not in self._cache:
            var_name = f"{self.name}_{'_'.join(map(str, key))}"
            self._cache[key] = sp.Symbol(var_name, binary=True)
        
        return self._cache[key]
    
    def get_all_variables(self):
        """Return all created variables as a sorted list."""
        return sorted(self._cache.values(), key=lambda s: s.name)
    

class PyToQ:
    """
    Converts Python expressions with sum() to upper triangular matrix Q.
    Skips linear terms.
    
    Example:
        builder = PyToQ()
        x = builder.create_variable_array('x')
        
        # Write natural Python:
        V = [10, 20]
        expr = sum(V[i] * x[i] for i in range(2))
        
        # Convert to Q Matrix:
        Q = builder.expression_to_q(expr)
    """
    
    def __init__(self):
        self.variable_arrays = {}
    
    def create_variable_array(self, name: str) -> SymbolicVariableArray:
        """
        Create a symbolic variable array.
        
        Args:
            name: Base name for variables (e.g., 'x')
            
        Returns:
            SymbolicVariableArray that can be indexed like x[i,j,k]
        """
        array = SymbolicVariableArray(name)
        self.variable_arrays[name] = array
        return array
    
    def expression_to_q(self, expr) -> Tuple[np.ndarray, Dict]:
        """
        Convert a SymPy expression to upper traingular matrix Q.
        
        Args:
            expr: SymPy expression (from evaluating your Python code)
            
        Returns:
            Q: QUBO upper traingular matrix (num_vars × num_vars)
            var_map: Dict mapping variable indices to Symbol names
        """
        all_vars = sorted(expr.free_symbols, key=lambda s: s.name)
        num_vars = len(all_vars)
        
        var_to_idx = {var: i for i, var in enumerate(all_vars)}
        idx_to_var = {i: var for i, var in enumerate(all_vars)}
        
        Q = np.zeros((num_vars, num_vars))
        
        expanded = sp.expand(expr)
        
        terms = expanded.as_coefficients_dict()

        for term, coeff in terms.items():

            # TODO: skipping costant terms

            if term == 1:
                continue
            
            term_vars = term.free_symbols
            
            if len(term_vars) == 0:
                # TODO: skipping costant terms
                continue
            elif len(term_vars) == 1:
                var = list(term_vars)[0]
                i = var_to_idx[var]
                Q[i, i] += float(coeff)
            elif len(term_vars) == 2:
                vars_list = sorted(term_vars, key=lambda s: s.name)
                i = var_to_idx[vars_list[0]]
                j = var_to_idx[vars_list[1]]
                
                if i > j:
                    i, j = j, i
                
                Q[i, j] += float(coeff)
            else:
                raise ValueError(
                    f"QUBO only supports quadratic terms!"
                    f"Found term with {len(term_vars)} variables: {term}"
                )
        
        return Q, idx_to_var

    def q_matrix_to_hamiltonian(self, Q: np.ndarray) -> SparsePauliOp:
        """
        Convert QUBO matrix Q to cost Hamiltonian.
        
        Formula:
            For diagonal Q[i,i]: add 0.5 * Q[i,i] * (I - Z_i)
            For off-diag Q[i,j]: add 0.25 * Q[i,j] * (I - Z_i - Z_j + Z_i*Z_j)
        
        We drop constant terms (all I's), so:
            Diagonal → -0.5 * Q[i,i] * Z_i
            Off-diag → 0.25 * Q[i,j] * Z_i*Z_j - 0.25*Q[i,j]*(Z_i + Z_j)
        """
        num_qubits = Q.shape[0]
        pauli_dict = {}
        pauli_list = []
        
        def make_pauli_string(positions: list, num_qubits: int) -> str:
            """
            Create Pauli string with Z at specified positions, I elsewhere.
            
            Example:
                make_pauli_string([0, 2], 4) → "ZIZI"
            """
            result = ['I'] * num_qubits
            for pos in positions:
                result[pos] = 'Z'
            return ''.join(result)
        
        for i in range(num_qubits):
            for j in range(i, num_qubits):
                if Q[i, j] == 0:
                    continue
                
                if i == j:
                    pauli_str = make_pauli_string([i], num_qubits)
                    pauli_dict[pauli_str] = pauli_dict.get(pauli_str, 0) + (-0.5 * Q[i,j])
                else:
                    pauli_str = make_pauli_string([i, j], num_qubits)
                    pauli_dict[pauli_str] = pauli_dict.get(pauli_str, 0) + (0.25 * Q[i,j])
                    
                    pauli_str = make_pauli_string([i], num_qubits)
                    pauli_dict[pauli_str] = pauli_dict.get(pauli_str, 0) + (-0.25 * Q[i,j])
                    
                    pauli_str = make_pauli_string([j], num_qubits)
                    pauli_dict[pauli_str] = pauli_dict.get(pauli_str, 0) + (-0.25 * Q[i,j])
        
        pauli_list = [(pauli_str, coeff) for pauli_str, coeff in pauli_dict.items()]
        
        return SparsePauliOp.from_list(pauli_list)
