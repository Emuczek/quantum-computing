from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import SparsePauliOp
from scipy.optimize import minimize
import numpy as np
from qaoa_circuit import QAOACircuit


class QAOAOptimizer:
    """Runs QAOA optimization loop using classical optimizer."""
    
    def __init__(
        self, 
        num_qubits: int,
        cost_hamiltonian: SparsePauliOp,
        p: int = 1
    ):
        self.num_qubits = num_qubits
        self.cost_hamiltonian = cost_hamiltonian
        self.p = p
        
        self.qaoa_circuit = QAOACircuit(num_qubits, cost_hamiltonian, p)
        
        self.estimator = StatevectorEstimator()
        self.sampler = StatevectorSampler()
        
        self.iteration = 0
        self.history = []
    
    def objective_function(self, params: np.ndarray) -> float:
        gamma = params[:self.p]
        beta = params[self.p:]
        
        circuit = self.qaoa_circuit.build_circuit(gamma, beta)
        
        job = self.estimator.run([(circuit, self.cost_hamiltonian)])
        result = job.result()
        
        data = result[0].data
        expectation = getattr(data, 'evs')

        self.iteration += 1
        self.history.append({
            'iteration': self.iteration,
            'params': params.copy(),
            'cost': expectation
        })
        
        if self.iteration % 10 == 0:
            print(f"Iteration {self.iteration}: cost = {expectation:.4f}")
        
        return expectation
    
    def optimize(self, method: str = 'COBYLA', maxiter: int = 100) -> dict:
        """
        Run QAOA optimization.
        
        Args:
            method: Classical optimization method ('COBYLA', 'SLSQP', etc.)
            maxiter: Maximum iterations
            
        Returns:
            Dictionary with optimization results
        """
        
        initial_params = np.random.uniform(0, 2*np.pi, size=2*self.p)
        
        print(f"Starting QAOA optimization with p={self.p}")
        print(f"Initial parameters: {initial_params}")
        print(f"Optimizer: {method}, Max iterations: {maxiter}\n")
        
        result = minimize(
            fun=self.objective_function,
            x0=initial_params,
            method=method,
            options={'maxiter': maxiter}
        )
        
        optimal_gamma = result.x[:self.p]
        optimal_beta = result.x[self.p:]
        
        print(f"\nOptimization complete!")
        print(f"Optimal gamma: {optimal_gamma}")
        print(f"Optimal beta: {optimal_beta}")
        print(f"Optimal cost: {result.fun:.4f}")
        
        return {
            'success': result.success,
            'optimal_params': result.x,
            'optimal_gamma': optimal_gamma,
            'optimal_beta': optimal_beta,
            'optimal_cost': result.fun,
            'num_iterations': getattr(result, 'nit', self.iteration),
            'history': self.history
        }
    
    def sample_solution(self, gamma: np.ndarray, beta: np.ndarray, shots: int = 1024) -> dict:
        """Sample measurement outcomes from optimized circuit."""
        circuit = self.qaoa_circuit.build_circuit(gamma, beta)
        circuit.measure_all()
        
        job = self.sampler.run([(circuit,)], shots=shots)
        result = job.result()
        
        data = result[0].data
        meas = getattr(data, 'meas')
        counts = meas.get_counts()
        
        return counts