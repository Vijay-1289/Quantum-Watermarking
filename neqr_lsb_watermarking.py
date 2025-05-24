import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

class NEQRLSBWatermarking:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("NEQR-LSB Watermarking Tool")
        self.window.geometry("1600x800")
        
        # Variables to store image paths
        self.host_image_path = None
        self.watermark_image_path = None
        self.watermarked_image = None
        
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
        self.upload_host_btn = tk.Button(left_frame, text="Upload Host Image", command=self.upload_host_image)
        self.upload_host_btn.pack(pady=10)
        
        self.upload_watermark_btn = tk.Button(left_frame, text="Upload Watermark Image", command=self.upload_watermark_image)
        self.upload_watermark_btn.pack(pady=10)
        
        self.embed_btn = tk.Button(left_frame, text="Embed Watermark", command=self.start_embedding)
        self.embed_btn.pack(pady=10)
        
        # Create progress bar
        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X)
        
        # Create right frame for images
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill='both', padx=10)
        
        # Create image display frames
        images_frame = tk.Frame(right_frame)
        images_frame.pack(expand=True, fill='both')
        
        # Host image frame
        host_frame = tk.Frame(images_frame)
        host_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=5)
        tk.Label(host_frame, text="Host Image").pack()
        self.host_label = tk.Label(host_frame)
        self.host_label.pack(expand=True)
        
        # Arrow frame 1
        arrow_frame1 = tk.Frame(images_frame)
        arrow_frame1.pack(side=tk.LEFT, fill='y', padx=5)
        tk.Label(arrow_frame1, text="→").pack(expand=True)
        
        # Watermark frame
        watermark_frame = tk.Frame(images_frame)
        watermark_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=5)
        tk.Label(watermark_frame, text="Watermark").pack()
        self.watermark_label = tk.Label(watermark_frame)
        self.watermark_label.pack(expand=True)
        
        # Arrow frame 2
        arrow_frame2 = tk.Frame(images_frame)
        arrow_frame2.pack(side=tk.LEFT, fill='y', padx=5)
        tk.Label(arrow_frame2, text="→").pack(expand=True)
        
        # Watermarked image frame
        watermarked_frame = tk.Frame(images_frame)
        watermarked_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=5)
        tk.Label(watermarked_frame, text="Watermarked Image").pack()
        self.watermarked_label = tk.Label(watermarked_frame)
        self.watermarked_label.pack(expand=True)
        
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
        
    def upload_host_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.host_image_path = file_path
            self.display_image(file_path, self.host_label)
            
            # Display matrix values of host image
            host_array = np.array(Image.open(file_path))
            self.display_matrix_values(host_array, "Host Image Matrix Values")
            
    def upload_watermark_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.watermark_image_path = file_path
            self.display_image(file_path, self.watermark_label)
            
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

    def apply_neqr_lsb(self, host_pixel, watermark_bit):
        # Create quantum circuit for NEQR-LSB
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
        
        # Encode pixel intensity
        intensity_binary = format(host_pixel, '08b')
        for i, bit in enumerate(intensity_binary):
            if bit == '1':
                qc.x(intensity_reg[i])
        
        # Apply LSB modification based on watermark bit
        if watermark_bit:
            qc.x(intensity_reg[7])  # Flip LSB if watermark bit is 1
        
        # Copy LSB to auxiliary qubit
        qc.cx(intensity_reg[7], aux_reg[0])
        
        # Measure the auxiliary qubit
        qc.measure(aux_reg[0], classical_reg[0])
        
        # Execute the circuit
        job = self.simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Get the measured value
        measured_value = int(list(counts.keys())[0])
        return measured_value

    def embed_watermark_thread(self):
        try:
            # Load images
            host_img = Image.open(self.host_image_path)
            watermark_img = Image.open(self.watermark_image_path)
            
            # Convert watermark to grayscale but keep host image in color
            watermark_img = watermark_img.convert('L')
            
            # Calculate appropriate watermark size (1/8 of host image)
            watermark_width = host_img.width // 4
            watermark_height = host_img.height // 4
            
            # Resize watermark
            watermark_img = watermark_img.resize((watermark_width, watermark_height))
            
            # Convert to numpy arrays
            host_array = np.array(host_img)
            watermark_array = np.array(watermark_img)
            
            # Display initial matrices
            self.display_matrix_values(host_array, "Initial Host Image Matrix")
            self.display_matrix_values(watermark_array, "Watermark Matrix")
            
            # Create output array
            watermarked_array = np.copy(host_array)
            
            # Process in chunks for better performance
            chunk_size = 1000
            total_pixels = watermark_width * watermark_height
            total_chunks = (total_pixels + chunk_size - 1) // chunk_size
            
            print("\nEmbedding watermark using NEQR-LSB...")
            for chunk in range(total_chunks):
                start_idx = chunk * chunk_size
                end_idx = min(start_idx + chunk_size, total_pixels)
                
                for i in range(start_idx, end_idx):
                    x = i // watermark_width
                    y = i % watermark_width
                    
                    # Get watermark bit
                    watermark_bit = 1 if watermark_array[x, y] > 127 else 0
                    
                    # Process each color channel
                    for c in range(host_array.shape[2] if len(host_array.shape) > 2 else 1):
                        if len(host_array.shape) > 2:  # Color image
                            host_pixel = host_array[x, y, c]
                            # Apply NEQR-LSB embedding to each channel
                            new_lsb = self.apply_neqr_lsb(host_pixel, watermark_bit)
                            watermarked_array[x, y, c] = (host_pixel & 254) | new_lsb
                        else:  # Grayscale image
                            host_pixel = host_array[x, y]
                            new_lsb = self.apply_neqr_lsb(host_pixel, watermark_bit)
                            watermarked_array[x, y] = (host_pixel & 254) | new_lsb
                
                # Update progress
                progress = (chunk + 1) / total_chunks * 100
                self.window.after(0, lambda p=progress: self.progress_var.set(p))
                
                # Display intermediate matrix values every 25% progress
                if progress % 25 == 0:
                    self.display_matrix_values(watermarked_array, f"Watermarked Image Matrix (Progress: {progress:.0f}%)")
            
            # Display final watermarked matrix
            self.display_matrix_values(watermarked_array, "Final Watermarked Image Matrix")
            
            # Convert back to image
            watermarked_img = Image.fromarray(watermarked_array)
            
            # Display watermarked image
            self.window.after(0, lambda: self.display_image(watermarked_img, self.watermarked_label))
            
            # Save watermarked image
            save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                    filetypes=[("PNG files", "*.png")])
            if save_path:
                watermarked_img.save(save_path)
                self.window.after(0, lambda: messagebox.showinfo("Success", 
                    "Watermark embedded successfully using NEQR-LSB!"))
                
        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.window.after(0, lambda: self.progress_var.set(0))
            
    def start_embedding(self):
        if not self.host_image_path or not self.watermark_image_path:
            messagebox.showerror("Error", "Please upload both host and watermark images")
            return
            
        # Disable buttons during processing
        self.embed_btn.config(state='disabled')
        self.upload_host_btn.config(state='disabled')
        self.upload_watermark_btn.config(state='disabled')
        
        # Start embedding in a separate thread
        thread = threading.Thread(target=self.embed_watermark_thread)
        thread.daemon = True
        thread.start()
        
        # Re-enable buttons after processing
        def reenable_buttons():
            self.embed_btn.config(state='normal')
            self.upload_host_btn.config(state='normal')
            self.upload_watermark_btn.config(state='normal')
        
        self.window.after(100, reenable_buttons)
            
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = NEQRLSBWatermarking()
    app.run()
