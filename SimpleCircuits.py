#Imports for 3 modes of execution: Real Hardware, Local Simulator, and Fake Backend
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as RealSampler
from qiskit_aer.primitives import SamplerV2 as AerSampler
from qiskit_aer.noise import NoiseModel
from qiskit.providers.fake_provider import GenericBackendV2

#Other imports
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from qiskit.visualization import plot_histogram
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_bloch_multivector


#======= MODE SELECTION SECTION: "REAL", "NOISY_SIM", "FAST_FAKE_LOCAL"     ==========================================
#======= Create a fake 127 qubit chip locally    ==========================================
MODE = "NOISY_SIM"
print(f"Initializing MODE: {MODE}")

if MODE == "REAL":
    # --- MODE 1: REAL HARDWARE ---
    # Costs money/quota. Long queue times.
    service = QiskitRuntimeService()
    backend = service.least_busy(min_num_qubits=127)
    print(f"   Connected to: {backend.name}")
    sampler = RealSampler(mode=backend)
elif MODE == "NOISY_SIM":
    # --- MODE 2: AER SIMULATOR (Real Noise Model) ---
    # Free, runs locally, but takes time to download noise data.
    service = QiskitRuntimeService()
    real_backend = service.least_busy(min_num_qubits=127)
    print(f"   Downloading noise model from: {real_backend.name}...")
    noise_model = NoiseModel.from_backend(real_backend)
    print("   Noise model built.")
    sampler = AerSampler(options={"backend_options": {"noise_model": noise_model}})
elif MODE == "FAST_FAKE_LOCAL":
    # --- MODE 3: AER SIMULATOR (Fake Backend) ---
    # Free, runs locally, but takes time to download noise data.
    fake_backend = GenericBackendV2(num_qubits=127) # Create a fake 127 qubit chip locally
    print(f"   Using fake backend: {fake_backend.name}")
    sampler = AerSampler()
else:
    raise ValueError("Invalid MODE selected. Choose REAL, NOISY_SIM, or FAST_FAKE_LOCAL")

# =================================================================================

# Simple Circuit 1: Add and Swap

def create_add_swap_circuit():
    q = QuantumRegister(4,"q")
    c = ClassicalRegister(2,"c")
    qc = QuantumCircuit(q,c)
    
    # Quantum Half Adder
    #Use NOT gates to initialize the qubits to 1
    qc.x(0)
    qc.x(1)
    #Add a barrier to separate between sections, so that the transpiler does not cancel out the gates and better optimize the circuit
    qc.barrier()
    #Apply CNOT gates to the qubits (CNOT is the quantum equivalent of the XOR gate)
    qc.cx(0,2)
    qc.cx(1,2)

    # Calculate the carry bit using a Toffoli gate (CCNOT)
    qc.ccx(0,1,3)
    qc.barrier()

    #Swap gate demonstration
    qc.swap(2,3)

    # measure the output qubits to check for correctness
    qc.measure(2,c[0])
    qc.measure(3,c[1])
    
    return qc

# Simple Circuit 2: Single Qubit Gates:H, S (Phase), Z, Y, RX/RY/RZ (Rotation)

def create_superposition_circuit():
    q = QuantumRegister(1, 'q')
    c = ClassicalRegister(1, 'c')
    qc = QuantumCircuit(q, c)
    
    # Step 1: Create Superposition (Hadamard) -> |+>
    qc.h(0)
    
    # Step 2: Phase Manipulation (S gate = 90 deg Z-rotation) -> |+i>
    qc.s(0)
    
    # Step 3: Flip it around (Y gate)
    qc.y(0)
    
    # Step 4: Fine-tuned Rotation (RX) - Arbitrary angle
    # Rotating by Pi/3 around X-axis
    qc.rx(np.pi/3, 0)
    

    qc.draw("mpl")
    plt.show()
    qc.measure(0, 0)
    return qc

def create_superposition_circuit_with_visualization():
    print("\n--- VISUALIZING SINGLE QUBIT MANIPULATION ---")
    
    # Start with |0>
    psi = Statevector.from_label('0')
    print("0. Initial State: |0>")
    fig = plot_bloch_multivector(psi, title="Initial |0>") 
    plt.show()

    # Step 1: Hadamard (H) -> |+> (Superposition)
    # H moves state from Z-axis (North Pole) to X-axis (Equator)
    qc_h = QuantumCircuit(1)
    qc_h.h(0)
    psi = psi.evolve(qc_h)   
    print("1. After Hadamard (H): Moves to X-axis |+>")
    plot_bloch_multivector(psi, title="After Hadamard (H)")
    plt.show()

    # Step 2: S Gate (Phase) -> |+i>
    # S rotates 90 degrees around Z-axis. Moves from X-axis to Y-axis.
    qc_s = QuantumCircuit(1)
    qc_s.s(0)
    psi = psi.evolve(qc_s)
    print("2. After S-Gate: Rotates 90° around Z-axis to Y-axis |+i>")
    plot_bloch_multivector(psi, title="After S-Gate") 
    plt.show()

    # Step 3: Y Gate -> |-i>
    # Y rotates 180° around Y-axis. Flips the state across the sphere.
    qc_y = QuantumCircuit(1)
    qc_y.y(0)
    psi = psi.evolve(qc_y)
    print("3. After Y-Gate: Flips 180° around Y-axis")
    plot_bloch_multivector(psi, title="After Y-Gate") 
    plt.show()

    # Step 4: RX(pi/3) -> Rotation
    # Rotates by 60 degrees around X-axis. Lifts vector off the equator.
    qc_rx = QuantumCircuit(1)
    qc_rx.rx(np.pi/3, 0)
    psi = psi.evolve(qc_rx)
    print("4. After RX(pi/3): Rotates 60° around X-axis (lifts up)")
    plot_bloch_multivector(psi, title="After RX(pi/3)") 
    plt.show()
 

    # Return a circuit for the actual hardware run (measurement added)
    qc_final = QuantumCircuit(1, 1)
    qc_final.h(0)
    qc_final.s(0)
    qc_final.y(0)
    qc_final.rx(np.pi/3, 0)
    qc_final.measure(0, 0)
    return qc_final

# Demonstrates: H, CX, T (pi/4 Phase), Dynamic Construction
def create_entanglement_circuit():
    circuits = []
    titles = []
    
    # First step: Standard Bell State Creation (|00> + |11>)
    qc1 = QuantumCircuit(2)
    qc1.h(0)
    qc1.measure_all()
    circuits.append(qc1)
    titles.append("Step 1: after H --> |00>+|01>")
    #Second step: after CNOT on Qubit 0 and 1
    qc2 = QuantumCircuit(2)
    qc2.h(0)
    qc2.cx(0, 1)
    qc2.measure_all()
    circuits.append(qc2)
    titles.append("Step 2: after CNOT --> |00>+|11>")
    #Third step: Bell + T (phase change, hidden in counts)
    qc3 = QuantumCircuit(2)
    qc3.h(0)
    qc3.cx(0, 1)
    qc3.t(1)
    qc3.measure_all()
    circuits.append(qc3)
    titles.append("Step 3: after T --> |00>+|11> + phase change")

    #Fourth step: Rotate Qubit 0 to see how entanglement persists
    qc4 = QuantumCircuit(2)
    qc4.h(0)
    qc4.cx(0, 1)
    qc4.t(1)
    qc4.ry(np.pi/2, 0)
    qc4.measure_all()
    circuits.append(qc4)
    titles.append("Step 4: after Ry(pi/2) --> |00>+|11> + phase change + RY(0)")

    return circuits, titles


# Execution playgrounds
# ======================== 1+1 half adder + swap circuit  ==================================

#     # Setup and draw the circuit
# print("Generating add and swap circuits...")
# add_swap_circuit = create_add_swap_circuit()
# add_swap_circuit.draw("mpl")
# plt.show()

#     #Run the circuit on simulator or real hardware
# job = sampler.run([add_swap_circuit])
# print("waiting for the result...")
# result = job.result()
# data_pub = result[0].data.c
# counts = data_pub.get_counts()
# plot_histogram(counts)
# plt.title("Add and Swap Circuit Results")
# plt.show()



# ======================== Single qubit Gates ==================================
# # Setup and draw the circuit
# qc_super = create_superposition_circuit()
# #Visualize the single qubit evolution on bloch sphere
# qc_super_visual = create_superposition_circuit_with_visualization()



# ======================== Entanglement Master: "The Bell-State Mixer" ==================================
circuits, titles = create_entanglement_circuit()

print("Drawing the last circuit...")
circuits[-1].draw("mpl")
plt.show()

print("Running the circuit on simulator or real hardware...")
job = sampler.run(circuits)
result = job.result()

for i, title in enumerate(titles):
    data_pub = result[i].data.meas
    counts = data_pub.get_counts()
    print(f"{title}: {counts}")
    plot_histogram(counts)
    plt.title(title)
    plt.show()
