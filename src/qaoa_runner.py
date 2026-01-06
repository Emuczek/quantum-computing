from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2, SamplerV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.quantum_info import SparsePauliOp
from scipy.optimize import minimize
import numpy as np
from qaoa_circuit import QAOACircuit
from typing import Literal


class QAOARunner:
    """
    Unified QAOA runner supporting both simulator and IBM hardware.
    
    Usage:
        # Simulator (free, fast):
        runner = QAOARunner(backend='simulator')
        
        # IBM hardware (costs credits):
        runner = QAOARunner(backend='ibm', device='ibm_brisbane')
    """
    
    def __init__(
        self,
        backend: Literal['simulator', 'ibm'] = 'simulator',
        device: str | None= None,
        ibm_token: str | None= None
    ):
        """
        Initialize QAOA runner.
        
        Args:
            backend: 'simulator' or 'ibm'
            device: IBM device name (e.g., 'ibm_brisbane', 'ibm_kyoto')
            ibm_token: IBM Quantum token (optional if already saved)
        """
        self.backend_type = backend
        
        if backend == 'simulator':
            print("Using local simulator (free, unlimited)")
            self.estimator = StatevectorEstimator()
            self.sampler = StatevectorSampler()
            self.transpile_needed = False
            
        elif backend == 'ibm':
            print("Connecting to IBM Quantum...")
            
            if ibm_token:
                service = QiskitRuntimeService(channel="ibm_quantum_platform", token=ibm_token)
            else:
                service = QiskitRuntimeService(channel="ibm_quantum_platform")

            if device:
                self.device = service.backend(device)
                print(f"   Connected to: {device}")
            else:
                self.device = service.least_busy(operational=True, simulator=False)
                print(f"   Auto-selected: {self.device.name}")

            status = getattr(self.device, "status")
            
            print(f"   Queue length: {status().pending_jobs}")
            print(f"   Qubits: {self.device.num_qubits}")
            
            self.estimator = EstimatorV2(self.device)
            self.sampler = SamplerV2(self.device)
            self.transpile_needed = True
            
            self.pass_manager = generate_preset_pass_manager(
                optimization_level=3,
                backend=self.device
            )
        
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def optimize(
        self,
        num_qubits: int,
        cost_hamiltonian: SparsePauliOp,
        p: int = 1,
        method: str = 'COBYLA',
        maxiter: int = 50,
        initial_params: np.ndarray | None = None
    ) -> dict:
        """
        Run QAOA optimization.
        
        Args:
            num_qubits: Number of qubits
            cost_hamiltonian: Problem Hamiltonian
            p: QAOA depth
            method: Classical optimizer
            maxiter: Maximum iterations
            initial_params: Starting parameters (optional)
            
        Returns:
            Results dictionary with optimal parameters and cost
        """
        qaoa_circuit = QAOACircuit(num_qubits, cost_hamiltonian, p)
        
        iteration = 0
        history = []
        
        def objective_function(params: np.ndarray) -> float:
            nonlocal iteration
            
            gamma = params[:p]
            beta = params[p:]
            
            circuit = qaoa_circuit.build_circuit(gamma, beta)
            
            if self.transpile_needed:
                circuit = self.pass_manager.run(circuit)
                obs = cost_hamiltonian.apply_layout(circuit.layout)
            else:
                obs = cost_hamiltonian
            
            job = self.estimator.run([(circuit, obs)])
            result = job.result()

            data = result[0].data
            evs = getattr(data, 'evs')
            expectation = evs
            
            iteration += 1
            history.append({
                'iteration': iteration,
                'params': params.copy(),
                'cost': expectation
            })
            
            if iteration % 10 == 0:
                print(f"  Iteration {iteration}: cost = {expectation:.4f}")
            
            return expectation
        
        if initial_params is None:
            initial_params = np.random.uniform(0, 2*np.pi, size=2*p)
        
        print(f"\nStarting QAOA optimization (p={p})")
        print(f"   Backend: {self.backend_type}")
        print(f"   Optimizer: {method}, Max iterations: {maxiter}")
        print(f"   Initial params: {initial_params}\n")
        
        result = minimize(
            fun=objective_function,
            x0=initial_params,
            method=method,
            options={'maxiter': maxiter}
        )
        
        optimal_gamma = result.x[:p]
        optimal_beta = result.x[p:]
        
        print(f"\nOptimization complete!")
        print(f"   Optimal gamma: {optimal_gamma}")
        print(f"   Optimal beta: {optimal_beta}")
        print(f"   Optimal cost: {result.fun:.4f}")
        print(f"   Total iterations: {iteration}")
        
        if self.backend_type == 'ibm':
            estimated_time = iteration * 20 
            print(f"Estimated quantum time used: {estimated_time:.1f} seconds")
        
        return {
            'success': result.success,
            'optimal_params': result.x,
            'optimal_gamma': optimal_gamma,
            'optimal_beta': optimal_beta,
            'optimal_cost': result.fun,
            'num_iterations': iteration,
            'history': history,
            'backend': self.backend_type
        }
    
    def sample_solution(
        self,
        num_qubits: int,
        cost_hamiltonian: SparsePauliOp,
        gamma: np.ndarray,
        beta: np.ndarray,
        shots: int = 1024,
        p: int = 1
    ) -> dict:
        """
        Sample final solution from optimized circuit.
        
        Returns:
            Dictionary of measurement counts
        """
        qaoa_circuit = QAOACircuit(num_qubits, cost_hamiltonian, p)
        circuit = qaoa_circuit.build_circuit(gamma, beta)
        circuit.measure_all()
        
        if self.transpile_needed:
            circuit = self.pass_manager.run(circuit)
        
        print(f"\nSampling solution ({shots} shots)...")
        
        job = self.sampler.run([(circuit,)], shots=shots)
        result = job.result()
        data = result[0].data
        meas = getattr(data, 'meas')
        counts = meas.get_counts()
        
        return counts