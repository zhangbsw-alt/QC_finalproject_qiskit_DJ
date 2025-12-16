import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt

# --- 1. The Oracle "Black Box" with a Counter ---
class Oracle:
    def __init__(self, n, oracle_type='balanced'):
        self.n = n
        self.type = oracle_type
        self.call_count = 0
        
        # Define the hidden function for classical access
        # Balanced: f(x) = x0 XOR x1 (parity of first two bits)
        # Constant: f(x) = 0
        self.hidden_function = lambda x: (int(x[0]) ^ int(x[1])) if oracle_type == 'balanced' else 0

    def query_classical(self, input_str):
        """Simulates querying the oracle classically (e.g., f('1010'))."""
        self.call_count += 1
        # Convert binary string to array-like access for our lambda
        # (Assuming input_str '1010' -> x[0]=1, x[1]=0...)
        return self.hidden_function(input_str)

    def get_quantum_circuit(self):
        """Returns the quantum gate wrapper for the oracle (counts as 1 call)."""
        self.call_count += 1
        qc = QuantumCircuit(self.n + 1)
        
        if self.type == 'balanced':
            # Implementation: CNOTs from q0, q1 to target (n)
            qc.cx(0, self.n)
            qc.cx(1, self.n)
        # If constant, do nothing
        return qc

# --- 2. The Classical Solver (Brute Force) ---
def solve_classical(n, oracle):
    print(f"  [Classical] Searching oracle of size 2^{n}...")
    
    # Generate all inputs (or enough to be sure)
    # Worst case: 2^(n-1) + 1
    limit = 2**(n-1) + 1
    results = []
    
    for i in range(2**n):
        # Format input as binary string, e.g., '0101'
        input_str = format(i, f'0{n}b')
        output = oracle.query_classical(input_str)
        results.append(output)
        
        # Check if we can stop early
        if len(results) > 1 and results[-1] != results[0]:
            print(f"  [Classical] Found difference after {oracle.call_count} queries. It's Balanced.")
            return 'balanced'
            
        if oracle.call_count >= limit:
            print(f"  [Classical] Checked {limit} entries (Worst Case). All same. It's Constant.")
            return 'constant'
            
    return 'constant' # Should happen at limit

# --- 3. The Quantum Solver (Deutsch-Jozsa) ---
def solve_quantum(n, oracle):
    print(f"  [Quantum]   Constructing circuit...")
    
    # 1. Setup Circuit
    qc = QuantumCircuit(n + 1, n)
    
    # 2. Superposition (H on inputs, XH on ancilla)
    qc.x(n)
    qc.h(n)
    for i in range(n):
        qc.h(i)
        
    # 3. Apply Oracle (This triggers the counter ONCE)
    oracle_gate = oracle.get_quantum_circuit()
    qc.compose(oracle_gate, inplace=True)
    
    # 4. Interference
    for i in range(n):
        qc.h(i)
        
    # 5. Measure
    qc.measure(range(n), range(n))
    qc.draw("mpl")
    plt.show()
    # 6. Run Simulation
    sim = AerSimulator()
    t_qc = transpile(qc, sim)
    result = sim.run(t_qc, shots=1).result()
    counts = result.get_counts()
    measured_state = list(counts.keys())[0] # e.g., '0000'
    
    # Logic: '00..0' -> Constant, Else -> Balanced
    print(f"  [Quantum]   Measured state: |{measured_state}>")
    if '1' in measured_state:
        return 'balanced'
    else:
        return 'constant'

# --- 4. The "Race" (Main Execution) ---
def run_race(n=4, oracle_type='balanced'):
    print(f"\n=== RACE: n={n} Qubits | Hidden Oracle is {oracle_type.upper()} ===")
    
    # Create distinct oracle instances so counts don't mix
    oracle_c = Oracle(n, oracle_type)
    oracle_q = Oracle(n, oracle_type)
    
    # Run Classical
    res_c = solve_classical(n, oracle_c)
    
    # Run Quantum
    res_q = solve_quantum(n, oracle_q)
    
    # Display Scoreboard
    print("-" * 40)
    print(f"FINAL SCOREBOARD (n={n})")
    print(f"Classical Queries Used: {oracle_c.call_count}")
    print(f"Quantum Queries Used:   {oracle_q.call_count}")
    print("-" * 40)

# Run the comparison
run_race(n=4, oracle_type='balanced')
run_race(n=4, oracle_type='constant')

