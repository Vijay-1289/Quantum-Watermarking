import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import Aer

# Initialize the Aer simulator
simulator = Aer.get_backend('aer_simulator')

# Sample 2x2 RGB image
color_image = np.array([
    [[120, 60, 30], [255, 128, 0]],
    [[0, 200, 100], [15, 45, 75]]
], dtype=np.uint8)

def apply_neqr_negation(pixel_rgb, position):
    """Applies NEQR negation to an RGB pixel (8-bit per channel)"""
    negated_rgb = []
    for channel_index, channel_value in enumerate(pixel_rgb):
        color_name = ['R', 'G', 'B'][channel_index]

        # Create quantum circuit
        qubits = QuantumRegister(8, f'{color_name.lower()}')
        classical_bits = ClassicalRegister(8, f'c_{color_name.lower()}')
        qc = QuantumCircuit(qubits, classical_bits)

        # Encode the original value
        binary_str = format(channel_value, '08b')
        for i, bit in enumerate(binary_str):
            if bit == '1':
                qc.x(qubits[i])

        # Apply X (NOT) gates to all bits for negation
        for i in range(8):
            qc.x(qubits[i])

        # Measure
        qc.measure(qubits, classical_bits)

        print(f"\nQuantum Circuit for pixel {position}, channel {color_name} (value: {channel_value}):")
        print(qc)

        # Transpile and simulate
        tqc = transpile(qc, simulator)
        result = simulator.run(tqc, shots=1).result()
        counts = result.get_counts()
        measured = int(list(counts.keys())[0], 2)
        negated_rgb.append(measured)
    return negated_rgb

# Negate the image
negated_image = np.zeros_like(color_image)

for i in range(2):
    for j in range(2):
        negated_pixel = apply_neqr_negation(color_image[i, j], position=(i, j))
        negated_image[i, j] = negated_pixel

print("\nOriginal Image (2x2 RGB):")
print(color_image)

print("\nNegated Image (2x2 RGB):")
print(negated_image)
