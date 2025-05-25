import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

class NEQRImageNegation:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("NEQR Image Negation (64x64)")
        self.window.geometry("1200x600")

        self.IMAGE_WIDTH = 64
        self.IMAGE_HEIGHT = 64
        self.input_text_path = None
        self.negated_image = None
        self.input_array = None
        self.simulator = AerSimulator()

        self.progress_var = tk.DoubleVar()
        self.progress_var.set(0)

        os.system('cls' if os.name == 'nt' else 'clear')

        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self.window)
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill='y', padx=10)

        self.upload_btn = tk.Button(left_frame, text="Upload Text File", command=self.upload_text_file)
        self.upload_btn.pack(pady=5)

        self.create_sample_btn = tk.Button(left_frame, text="Create Sample Text File", command=self.create_sample_file)
        self.create_sample_btn.pack(pady=5)

        self.negate_btn = tk.Button(left_frame, text="Negate Image", command=self.start_negation)
        self.negate_btn.pack(pady=5)

        self.save_text_btn = tk.Button(left_frame, text="Save as Text", command=self.save_as_text)
        self.save_text_btn.pack(pady=5)

        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill='both', padx=10)

        images_frame = tk.Frame(right_frame)
        images_frame.pack(expand=True, fill='both')

        input_frame = tk.Frame(images_frame)
        input_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=5)
        tk.Label(input_frame, text="Input Image (64x64)").pack()
        self.input_label = tk.Label(input_frame)
        self.input_label.pack(expand=True)

        arrow_frame = tk.Frame(images_frame)
        arrow_frame.pack(side=tk.LEFT, fill='y', padx=5)
        tk.Label(arrow_frame, text="→").pack(expand=True)

        negated_frame = tk.Frame(images_frame)
        negated_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=5)
        tk.Label(negated_frame, text="Negated Image (64x64)").pack()
        self.negated_label = tk.Label(negated_frame)
        self.negated_label.pack(expand=True)

    def create_sample_file(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                title="Save Sample Image Text File"
            )
            if not file_path:
                return

            sample_array = np.zeros((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint8)
            for i in range(self.IMAGE_HEIGHT):
                for j in range(self.IMAGE_WIDTH):
                    sample_array[i, j] = (i * 4) % 256

            self.image_to_text(sample_array, file_path)
            self.input_text_path = file_path
            self.input_array = sample_array

            sample_image = Image.fromarray(sample_array)
            self.display_image(sample_image, self.input_label)
            self.display_matrix_values(sample_array, "Sample Image Matrix Values")

            messagebox.showinfo("Success", "Sample text file created successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error creating sample file: {str(e)}")

    def text_to_image(self, text_file_path):
        """Load actual grayscale pixel values from .txt file."""
        try:
            with open(text_file_path, 'r') as f:
                lines = f.readlines()

            if len(lines[0].split()) == 2:  # skip dimensions if present
                lines = lines[1:]

            image_array = np.array([
                list(map(int, line.strip().split()))
                for line in lines[:self.IMAGE_HEIGHT]
            ], dtype=np.uint8)

            if image_array.shape != (self.IMAGE_HEIGHT, self.IMAGE_WIDTH):
                raise ValueError("Image dimensions do not match expected 64x64")

            return image_array

        except Exception as e:
            raise ValueError(f"Error parsing grayscale image text: {e}")

    def image_to_text(self, image_array, output_path):
        with open(output_path, 'w') as f:
            f.write(f"{self.IMAGE_HEIGHT} {self.IMAGE_WIDTH}\n")
            for row in image_array:
                f.write(' '.join(map(str, row)) + '\n')

    def display_matrix_values(self, array, title, max_rows=5, max_cols=5):
        print(f"\n{title}")
        print("-" * 50)
        height, width = array.shape
        print(f"Shape: {height}x{width}")
        for i in range(min(max_rows, height)):
            for j in range(min(max_cols, width)):
                print(f"{array[i,j]:3d}", end=" ")
            if width > max_cols:
                print("...", end="")
            print()
        if height > max_rows:
            print("...")
        print("-" * 50)

    def upload_text_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                self.input_text_path = file_path
                self.input_array = self.text_to_image(file_path)
                input_image = Image.fromarray(self.input_array)
                self.display_image(input_image, self.input_label)
                self.display_matrix_values(self.input_array, "Input Image Matrix Values")
            except Exception as e:
                messagebox.showerror("Error", f"Error reading text file: {str(e)}")

    def display_image(self, image, label, size=(300, 300)):
        image = image.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        label.configure(image=photo)
        label.image = photo

    def apply_neqr_negation(self, pixel_value, print_circuit=False):
        intensity_qubits = 8
        intensity_reg = QuantumRegister(intensity_qubits, 'intensity')
        classical_reg = ClassicalRegister(intensity_qubits, 'c')
        qc = QuantumCircuit(intensity_reg, classical_reg)

        # Encode pixel as binary
        binary_value = format(pixel_value, '08b')
        for i, bit in enumerate(binary_value):
            if bit == '1':
                qc.x(intensity_reg[i])

        # Negate using X gates
        for i in range(intensity_qubits):
            qc.x(intensity_reg[i])

        qc.measure(intensity_reg, classical_reg)

        if print_circuit:
            print(f"\nQuantum Circuit for pixel value {pixel_value}:")
            print(qc)

        job = self.simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        measured_value = int(list(counts.keys())[0], 2)
        return measured_value

    def negate_image_thread(self):
        try:
            if self.input_array is None:
                raise ValueError("No input image data available")

            height, width = self.input_array.shape
            negated_array = np.zeros((height, width), dtype=np.uint8)

            print("\nNegating image using NEQR quantum circuits...")
            for x in range(height):
                for y in range(width):
                    print_circuit = (x == 0 and y < 5)
                    negated_array[x, y] = self.apply_neqr_negation(self.input_array[x, y], print_circuit)
                progress = ((x + 1) / height) * 100
                self.window.after(0, lambda p=progress: self.progress_var.set(p))

            self.negated_image = Image.fromarray(negated_array)
            self.display_matrix_values(negated_array, "Final Negated Image Matrix")
            self.window.after(0, lambda: self.display_image(self.negated_image, self.negated_label))

        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.window.after(0, lambda: self.progress_var.set(0))

    def save_as_text(self):
        if self.negated_image is None:
            messagebox.showerror("Error", "Please negate the image first")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt")],
                                                 title="Save negated image as text")
        if save_path:
            try:
                negated_array = np.array(self.negated_image)
                self.image_to_text(negated_array, save_path)
                messagebox.showinfo("Success", "Negated image saved as text file successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving text file: {str(e)}")

    def start_negation(self):
        if self.input_array is None:
            messagebox.showerror("Error", "Please upload or create a text file first")
            return

        self.negate_btn.config(state='disabled')
        self.upload_btn.config(state='disabled')
        self.save_text_btn.config(state='disabled')
        self.create_sample_btn.config(state='disabled')

        thread = threading.Thread(target=self.negate_image_thread)
        thread.daemon = True
        thread.start()

        def reenable_buttons():
            self.negate_btn.config(state='normal')
            self.upload_btn.config(state='normal')
            self.save_text_btn.config(state='normal')
            self.create_sample_btn.config(state='normal')

        self.window.after(100, reenable_buttons)

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = NEQRImageNegation()
    app.run()
