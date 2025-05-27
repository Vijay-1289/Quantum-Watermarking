from PIL import Image, ImageDraw, ImageFont
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import numpy as np

# --- Convert int to bits ---
def int_to_bits(value, num_bits):
    return [int(bit) for bit in bin(value)[2:].zfill(num_bits)]

# --- Classical pixel negation ---
def classical_negate_pixel(value):
    return 255 - value

# --- Quantum pixel negation ---
def negate_pixel(value, bits, qc, qr, cr, offset=0):
    binary = int_to_bits(value, bits)
    for j in range(bits):
        if binary[bits - 1 - j] == 1:
            qc.x(qr[offset + j])
    qc.barrier()
    for j in range(bits):
        qc.x(qr[offset + j])
    qc.barrier()
    qc.measure(qr[offset:offset + bits], cr[offset:offset + bits])

# --- Save images side by side ---
def save_side_by_side_images(original_img, negated_img, output_path):
    width, height = original_img.size
    combined = Image.new("RGB", (width * 2 + 40, height + 40), (255, 255, 255))

    original_rgb = original_img.convert("RGB")
    negated_rgb = negated_img.convert("RGB")
    combined.paste(original_rgb, (20, 30))
    combined.paste(negated_rgb, (width + 30, 30))

    draw = ImageDraw.Draw(combined)
    font = ImageFont.load_default()
    draw.text((20, 10), "Original", fill=(0, 0, 0), font=font)
    draw.text((width + 30, 10), "Quantum Negated", fill=(0, 0, 0), font=font)

    combined.save(output_path)
    print(f"[✔] Side-by-side image saved: {output_path}")

# --- Convert text to grayscale matrix ---
def text_file_to_grayscale_matrix(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = [line.rstrip('\n') for line in file if line.strip()]
    matrix = [[ord(char) for char in line] for line in lines]
    return matrix

# --- Create image from grayscale matrix ---
def matrix_to_image(matrix):
    height = len(matrix)
    width = len(matrix[0])
    img = Image.new("L", (width, height))
    for y in range(height):
        for x in range(width):
            img.putpixel((x, y), matrix[y][x])
    return img

# --- Quantum grayscale negation ---
def quantum_negate_grayscale_matrix(matrix, bits=8):
    height = len(matrix)
    width = len(matrix[0])
    quantum_negated = [[0 for _ in range(width)] for _ in range(height)]
    printed_circuits = 0

    for r in range(height):
        for c in range(width):
            val = matrix[r][c]
            qr = QuantumRegister(bits, "q")
            cr = ClassicalRegister(bits, "c")
            qc = QuantumCircuit(qr, cr)
            negate_pixel(val, bits, qc, qr, cr)

            if printed_circuits < 8:
                print(f"\nQuantum Circuit for pixel ({r},{c}) value {val}:")
                print(qc.draw(output="text"))
                printed_circuits += 1

            backend = AerSimulator()
            job = backend.run(qc, shots=1)
            counts = job.result().get_counts()
            bitstring = list(counts.keys())[0]
            quantum_negated[r][c] = int(bitstring, 2)

    return quantum_negated

# --- Mean Squared Error ---
def calculate_mse(image1, image2):
    np1 = np.array(image1, dtype=np.float32)
    np2 = np.array(image2, dtype=np.float32)
    mse = np.mean((np1 - np2) ** 2)
    return mse

# --- Main Execution ---
if __name__ == "__main__":
    text_file = "lincon_rotated.txt"

    print("\nReading text and converting to grayscale image...")
    ascii_matrix = text_file_to_grayscale_matrix(text_file)
    orig_img = matrix_to_image(ascii_matrix)

    # Classical Negation for MSE comparison
    classical_negated_matrix = [[classical_negate_pixel(val) for val in row] for row in ascii_matrix]
    classical_negated_img = matrix_to_image(classical_negated_matrix)

    print("\nRunning quantum negation on grayscale image...")
    quantum_negated_matrix = quantum_negate_grayscale_matrix(ascii_matrix, bits=8)
    quantum_negated_img = matrix_to_image(quantum_negated_matrix)

    # Calculate MSE between classical and quantum negated images
    mse = calculate_mse(classical_negated_img, quantum_negated_img)
    print(f"\n[✓] MSE between classical and quantum negated images: {mse:.2f}")

    # Save image
    save_path = "text_quantum_negated_side_by_side.png"
    save_side_by_side_images(orig_img, quantum_negated_img, save_path)
