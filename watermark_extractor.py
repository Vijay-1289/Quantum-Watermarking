import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import threading
import os

class WaQIExtractor:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("WaQI Watermark Extractor")
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

    def apply_reverse_waqi(self, pixel_value):
        # Create quantum circuit with 3 qubits for reverse WaQI
        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        circuit = QuantumCircuit(qr, cr)
        
        # Initialize first qubit with pixel value
        if pixel_value & 1:
            circuit.x(0)
            
        # Apply reverse WaQI gates
        circuit.cx(1, 2)  # Reverse CNOT
        circuit.cx(0, 1)  # Reverse CNOT
        circuit.h(0)      # Hadamard gate
        
        # Measure the qubits
        circuit.measure(qr, cr)
        
        # Execute the circuit
        job = self.simulator.run(circuit, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Get the measured value and apply reverse transformation
        measured_value = int(list(counts.keys())[0], 2)
        return (measured_value >> 1) & 1  # Extract the watermark bit

    def extract_watermark_thread(self):
        try:
            # Load watermarked image
            watermarked_img = Image.open(self.watermarked_image_path)
            watermarked_array = np.array(watermarked_img)
            
            # Display initial watermarked image matrix
            self.display_matrix_values(watermarked_array, "Initial Watermarked Image Matrix")
            
            # Calculate watermark size (1/8 of watermarked image)
            watermark_width = watermarked_img.width // 4
            watermark_height = watermarked_img.height // 4
            
            # Create array for extracted watermark
            watermark_bits = []
            
            # Process in chunks for better performance
            chunk_size = 1000
            total_bits = watermark_width * watermark_height  # 1 bit per pixel
            total_chunks = (total_bits + chunk_size - 1) // chunk_size
            
            print("\nExtracting watermark...")
            for chunk in range(total_chunks):
                start_idx = chunk * chunk_size
                end_idx = min(start_idx + chunk_size, total_bits)
                
                for i in range(start_idx, end_idx):
                    pixel_value = watermarked_array.flat[i]
                    watermark_bit = self.apply_reverse_waqi(pixel_value)
                    watermark_bits.append(watermark_bit)
                
                # Update progress
                progress = (chunk + 1) / total_chunks * 100
                self.window.after(0, lambda p=progress: self.progress_var.set(p))
                
                # Display intermediate matrix values every 25% progress
                if progress % 25 == 0:
                    print(f"\nExtraction Progress: {progress:.0f}%")
            
            # Convert bits to image (binary)
            watermark_bits = np.array(watermark_bits, dtype=np.uint8)
            watermark_image = watermark_bits.reshape((watermark_height, watermark_width)) * 255
            extracted_watermark = Image.fromarray(watermark_image.astype(np.uint8), mode='L')
            
            # Display extracted watermark matrix
            self.display_matrix_values(np.array(extracted_watermark), "Extracted Watermark Matrix")
            
            # Display extracted watermark
            self.window.after(0, lambda: self.display_image(extracted_watermark, self.extracted_label))
            
            # Reconstruct original image
            original_array = np.copy(watermarked_array)
            for i in range(total_bits):
                original_array.flat[i] = (original_array.flat[i] & 254)  # Clear LSB
            
            # Display original image matrix
            self.display_matrix_values(original_array, "Reconstructed Original Image Matrix")
            
            original_image = Image.fromarray(original_array)
            
            # Display original image
            self.window.after(0, lambda: self.display_image(original_image, self.original_label))
            
            # Save extracted watermark and original image
            save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                    filetypes=[("PNG files", "*.png")])
            if save_path:
                extracted_watermark.save(save_path)
                original_path = save_path.replace('.png', '_original.png')
                original_image.save(original_path)
                self.window.after(0, lambda: messagebox.showinfo("Success", 
                    "Watermark extracted and original image reconstructed successfully!"))
                
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
    app = WaQIExtractor()
    app.run() 