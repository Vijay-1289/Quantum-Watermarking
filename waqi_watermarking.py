import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import threading
import os

class WaQIWatermarking:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("WaQI Watermarking Tool")
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
        
    def upload_host_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.host_image_path = file_path
            self.display_image(file_path, self.host_label)
            
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

    def apply_waqi_embedding(self, host_pixel, watermark_bit):
        # Create quantum circuit with 3 qubits for WaQI
        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        circuit = QuantumCircuit(qr, cr)
        
        # Initialize qubits based on host pixel and watermark bit
        if host_pixel & 1:
            circuit.x(0)
        if watermark_bit:
            circuit.x(1)
            
        # Apply WaQI specific gates
        circuit.h(0)  # Hadamard gate on first qubit
        circuit.cx(0, 1)  # CNOT between first and second qubit
        circuit.cx(1, 2)  # CNOT between second and third qubit
        
        # Measure the qubits
        circuit.measure(qr, cr)
        
        # Execute the circuit
        job = self.simulator.run(circuit, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Get the measured value and apply WaQI transformation
        measured_value = int(list(counts.keys())[0], 2)
        return (measured_value & 1) ^ ((measured_value >> 1) & 1)  # XOR of first two bits

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

    def embed_watermark_thread(self):
        try:
            # Load images
            host_img = Image.open(self.host_image_path)
            watermark_img = Image.open(self.watermark_image_path)
            
            # Convert host image to array and display original matrix
            host_array = np.array(host_img)
            self.display_matrix_values(host_array, "Original Image Matrix Values")
            
            # Convert watermark to binary
            watermark_img = watermark_img.convert('L')
            
            # Calculate appropriate watermark size (1/8 of host image)
            watermark_width = host_img.width // 4
            watermark_height = host_img.height // 4
            
            # Resize watermark
            watermark_img = watermark_img.resize((watermark_width, watermark_height))
            watermark_array = np.array(watermark_img)
            watermark_binary = np.unpackbits(watermark_array)
            
            # Calculate total bits needed
            total_bits_needed = watermark_binary.size
            total_bits_available = host_array.size
            
            if total_bits_available < total_bits_needed:
                self.window.after(0, lambda: messagebox.showerror("Error", 
                    f"Host image is too small for the watermark.\n"
                    f"Required bits: {total_bits_needed}\n"
                    f"Available bits: {total_bits_available}"))
                return
            
            # Create output array
            watermarked_array = np.copy(host_array)
            
            # Process in chunks for better performance
            chunk_size = 1000
            total_chunks = (total_bits_needed + chunk_size - 1) // chunk_size
            
            print("\nEmbedding watermark...")
            for chunk in range(total_chunks):
                start_idx = chunk * chunk_size
                end_idx = min(start_idx + chunk_size, total_bits_needed)
                
                for i in range(start_idx, end_idx):
                    pixel_value = host_array.flat[i]
                    watermark_bit = watermark_binary[i]
                    new_lsb = self.apply_waqi_embedding(pixel_value, watermark_bit)
                    watermarked_array.flat[i] = (pixel_value & 254) | new_lsb
                
                # Update progress
                progress = (chunk + 1) / total_chunks * 100
                self.window.after(0, lambda p=progress: self.progress_var.set(p))
                
                # Display intermediate matrix values every 25% progress
                if progress % 25 == 0:
                    self.display_matrix_values(watermarked_array, f"Watermarked Image Matrix Values (Progress: {progress:.0f}%)")
            
            # Display final watermarked matrix
            self.display_matrix_values(watermarked_array, "Final Watermarked Image Matrix Values")
            
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
                    "Watermark embedded successfully using WaQI!"))
                
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
    app = WaQIWatermarking()
    app.run() 