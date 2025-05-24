import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

class NEQRLSBExtractor:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("NEQR-LSB Watermark Extractor")
        self.window.geometry("1600x800")
        
        # Variables to store image paths
        self.watermarked_image_path = None
        self.extracted_watermark = None
        self.original_image = None
        
        # Initialize quantum simulator
        self.simulator = AerSimulator()
        
        # Progress tracking
        self.progress_var = tk.DoubleVar()
        self.progress_var.set(0)
        
        # Clear terminal
        os.system('cls' if os.name == 'nt' else 'clear')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create main frame
        main_frame = tk.Frame(self.window)
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Create left frame for controls
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill='y', padx=10)
        
        # Create buttons
        self.upload_btn = tk.Button(left_frame, text="Upload Watermarked Image", command=self.upload_image)
        self.upload_btn.pack(pady=10)
        
        self.extract_btn = tk.Button(left_frame, text="Extract Watermark", command=self.start_extraction)
        self.extract_btn.pack(pady=10)
        
        # Create progress bar
        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X)
        
        # Create right frame for images
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill='both', padx=10)
        
        # Create image display frames
        images_frame = tk.Frame(right_frame)
        images_frame.pack(expand=True, fill='both')
        
        # Watermarked image frame
        watermarked_frame = tk.Frame(images_frame)
        watermarked_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=5)
        tk.Label(watermarked_frame, text="Watermarked Image").pack()
        self.watermarked_label = tk.Label(watermarked_frame)
        self.watermarked_label.pack(expand=True)
        
        # Arrow frame 1
        arrow_frame1 = tk.Frame(images_frame)
        arrow_frame1.pack(side=tk.LEFT, fill='y', padx=5)
        tk.Label(arrow_frame1, text="→").pack(expand=True)
        
        # Extracted watermark frame
        extracted_frame = tk.Frame(images_frame)
        extracted_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=5)
        tk.Label(extracted_frame, text="Extracted Watermark").pack()
        self.extracted_label = tk.Label(extracted_frame)
        self.extracted_label.pack(expand=True)
        
        # Arrow frame 2
        arrow_frame2 = tk.Frame(images_frame)
        arrow_frame2.pack(side=tk.LEFT, fill='y', padx=5)
        tk.Label(arrow_frame2, text="→").pack(expand=True)
        
        # Original image frame
        original_frame = tk.Frame(images_frame)
        original_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=5)
        tk.Label(original_frame, text="Original Image").pack()
        self.original_label = tk.Label(original_frame)
        self.original_label.pack(expand=True)
        
    def display_matrix_values(self, array, title, max_rows=5, max_cols=5):
        """Display matrix values in a formatted way"""
        print(f"\n{title}")
        print("-" * 50)
        
        # Get dimensions
        if len(array.shape) == 3:  # Color image
            height, width, channels = array.shape
            print(f"Shape: {height}x{width}x{channels}")
            
            # Display a portion of the matrix
            for i in range(min(max_rows, height)):
                for j in range(min(max_cols, width)):
                    pixel = array[i, j]
                    print(f"Pixel[{i},{j}]: R={pixel[0]}, G={pixel[1]}, B={pixel[2]}")
                if j < width - 1:
                    print("...")
                print()
            if i < height - 1:
                print("...")
        else:  # Grayscale image
            height, width = array.shape
            print(f"Shape: {height}x{width}")
            
            # Display a portion of the matrix
            for i in range(min(max_rows, height)):
                for j in range(min(max_cols, width)):
                    print(f"{array[i,j]:3d}", end=" ")
                if j < width - 1:
                    print("...", end="")
                print()
            if i < height - 1:
                print("...")
        print("-" * 50)
        
    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.watermarked_image_path = file_path
            self.display_image(file_path, self.watermarked_label)
            
            # Display matrix values of watermarked image
            watermarked_array = np.array(Image.open(file_path))
            self.display_matrix_values(watermarked_array, "Watermarked Image Matrix Values")
            
    def display_image(self, image_path, label, size=(200, 200)):
        # Load and resize image for preview
        if isinstance(image_path, str):
            image = Image.open(image_path)
        else:
            image = image_path
        image = image.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        label.configure(image=photo)
        label.image = photo

    def apply_reverse_neqr_lsb(self, watermarked_pixel):
        # Create quantum circuit for reverse NEQR-LSB
        x_qubits = 2  # For x position
        y_qubits = 2  # For y position
        intensity_qubits = 8  # For pixel intensity
        aux_qubits = 1  # Auxiliary qubit for LSB
        
        # Initialize quantum registers
        pos_reg = QuantumRegister(x_qubits + y_qubits, 'pos')
        intensity_reg = QuantumRegister(intensity_qubits, 'intensity')
        aux_reg = QuantumRegister(aux_qubits, 'aux')
        classical_reg = ClassicalRegister(1, 'c')
        
        # Create quantum circuit
        qc = QuantumCircuit(pos_reg, intensity_reg, aux_reg, classical_reg)
        
        # Encode watermarked pixel intensity
        intensity_binary = format(watermarked_pixel, '08b')
        for i, bit in enumerate(intensity_binary):
            if bit == '1':
                qc.x(intensity_reg[i])
        
        # Apply reverse NEQR operations
        qc.h(0)  # Apply Hadamard gate first
        qc.cx(intensity_reg[7], aux_reg[0])  # Copy LSB to auxiliary qubit
        qc.cx(aux_reg[0], intensity_reg[7])  # Reverse the LSB modification
        
        # Measure the auxiliary qubit
        qc.measure(aux_reg[0], classical_reg[0])
        
        # Execute the circuit
        job = self.simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Get the measured value (watermark bit)
        measured_value = int(list(counts.keys())[0])
        return measured_value

    def extract_watermark_thread(self):
        try:
            # Load watermarked image
            watermarked_img = Image.open(self.watermarked_image_path)
            watermarked_array = np.array(watermarked_img)
            is_color = len(watermarked_array.shape) == 3 and watermarked_array.shape[2] >= 3
            num_channels = watermarked_array.shape[2] if is_color else 1
            height, width = watermarked_img.height, watermarked_img.width
            watermark_height = height // 4
            watermark_width = width // 4

            # Display initial watermarked image matrix
            self.display_matrix_values(watermarked_array, "Initial Watermarked Image Matrix")

            # Prepare arrays for extracted watermark and original image
            if is_color:
                watermark_bits = np.zeros((watermark_height, watermark_width, 3), dtype=np.uint8)
                original_array = np.copy(watermarked_array)
            else:
                watermark_bits = np.zeros((watermark_height, watermark_width), dtype=np.uint8)
                original_array = np.copy(watermarked_array)

            print(f"\nExtracting watermark using reverse NEQR-LSB... (is_color={is_color}, num_channels={num_channels})")
            for x in range(watermark_height):
                for y in range(watermark_width):
                    if is_color:
                        for c in range(3):  # Only use first 3 channels (RGB)
                            try:
                                watermarked_pixel = watermarked_array[x, y, c]
                                watermark_bits[x, y, c] = int(watermarked_pixel & 1) * 255
                                original_array[x, y, c] = int(watermarked_pixel & 254)
                            except Exception as e:
                                print(f"Error at (x={x}, y={y}, c={c}): pixel={watermarked_array[x, y, c]}, shape={watermarked_array.shape}")
                                raise e
                    else:
                        try:
                            watermarked_pixel = watermarked_array[x, y]
                            watermark_bits[x, y] = int(watermarked_pixel & 1) * 255
                            original_array[x, y] = int(watermarked_pixel & 254)
                        except Exception as e:
                            print(f"Error at (x={x}, y={y}): pixel={watermarked_array[x, y]}, shape={watermarked_array.shape}")
                            raise e
                progress = ((x + 1) / watermark_height) * 100
                self.window.after(0, lambda p=progress: self.progress_var.set(p))
                if progress % 25 == 0:
                    self.display_matrix_values(watermark_bits, f"Intermediate Watermark Matrix (Progress: {progress:.0f}%)")

            # Convert bits to image
            if is_color:
                extracted_watermark = Image.fromarray(watermark_bits, mode='RGB')
                # If original image has 4 channels, preserve alpha
                if num_channels == 4:
                    alpha_channel = watermarked_array[:watermark_height, :watermark_width, 3]
                    rgba = np.dstack((watermark_bits, alpha_channel))
                    extracted_watermark = Image.fromarray(rgba, mode='RGBA')
                    original_image = Image.fromarray(original_array, mode='RGBA')
                else:
                    original_image = Image.fromarray(original_array, mode='RGB')
            else:
                extracted_watermark = Image.fromarray(watermark_bits)
                original_image = Image.fromarray(original_array)

            # Display extracted watermark matrix
            self.display_matrix_values(np.array(extracted_watermark), "Extracted Watermark Matrix")

            # Display extracted watermark
            self.window.after(0, lambda: self.display_image(extracted_watermark, self.extracted_label))

            # Display original image matrix
            self.display_matrix_values(np.array(original_image), "Reconstructed Original Image Matrix")

            # Display original image
            self.window.after(0, lambda: self.display_image(original_image, self.original_label))

            # Save only the reconstructed original image
            save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                    filetypes=[("PNG files", "*.png")],
                                                    title="Save the reconstructed original image")
            if save_path:
                original_image.save(save_path)
                self.window.after(0, lambda: messagebox.showinfo("Success", 
                    "Original image reconstructed and saved successfully!"))

        except Exception as e:
            error_msg = str(e)
            self.window.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {error_msg}"))
        finally:
            self.window.after(0, lambda: self.progress_var.set(0))
            
    def start_extraction(self):
        if not self.watermarked_image_path:
            messagebox.showerror("Error", "Please upload a watermarked image")
            return
            
        # Disable buttons during processing
        self.extract_btn.config(state='disabled')
        self.upload_btn.config(state='disabled')
        
        # Start extraction in a separate thread
        thread = threading.Thread(target=self.extract_watermark_thread)
        thread.daemon = True
        thread.start()
        
        # Re-enable buttons after processing
        def reenable_buttons():
            self.extract_btn.config(state='normal')
            self.upload_btn.config(state='normal')
        
        self.window.after(100, reenable_buttons)
            
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = NEQRLSBExtractor()
    app.run() 