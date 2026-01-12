from qiskit_ibm_runtime import QiskitRuntimeService

IBM_TOKEN = "" 
CRN = ""

QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",
    token=IBM_TOKEN,
    instance=CRN,
    overwrite=True,
)

print("✅ IBM credentials saved!")