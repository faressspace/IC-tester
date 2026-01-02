import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import time
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from PIL import Image, ImageTk
import os
import io
import base64
from datetime import datetime
import pymongo
from bson.binary import Binary


class MongoDBICTesterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("IC Tester")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 800)

        # Variables
        self.port_var = tk.StringVar(value="COM4")
        self.baudrate_var = tk.StringVar(value="9600")
        self.mongo_uri_var = tk.StringVar(
            value="mongodb+srv://Group23:<db_password>@cluster0.mh3csnt.mongodb.net/?appName=Cluster0")
        self.db_name_var = tk.StringVar(value="ic_tester")
        self.collection_name_var = tk.StringVar(value="ic_database")

        self.collecting = False
        self.serial_conn = None
        self.messages = []
        self.current_buffer = []
        self.averaged_array = []
        self.comparison_results = []
        self.current_photo = None
        self.current_image = None

        # MongoDB connection
        self.mongo_client = None
        self.db = None
        self.collection = None

        self.setup_ui()
        self.connect_mongodb()

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(1, weight=1)

        # Title Header
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))

        title_label = tk.Label(title_frame, text="IC Tester",
                               font=("Arial", 18, "bold"))
        title_label.pack()

        info_frame = ttk.Frame(title_frame)
        info_frame.pack(pady=(10, 0))

        group_label = tk.Label(info_frame, text="Group 23",
                               font=("Arial", 12, "bold"),
                               fg="blue")
        group_label.pack(side=tk.LEFT, padx=(0, 20))

        supervisor_label = tk.Label(info_frame, text="Dr. Hossam El-Din Moustafa",
                                    font=("Arial", 12, "bold"),
                                    fg="darkgreen")
        supervisor_label.pack(side=tk.RIGHT)

        # Left panel - Controls
        left_panel = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_panel.columnconfigure(1, weight=1)

        row = 0

        # MongoDB Settings
        ttk.Label(left_panel, text="MongoDB URI:", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        row += 1

        mongo_uri_entry = ttk.Entry(left_panel, textvariable=self.mongo_uri_var)
        mongo_uri_entry.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1

        ttk.Label(left_panel, text="Database:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(left_panel, textvariable=self.db_name_var).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        row += 1

        ttk.Label(left_panel, text="Collection:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(left_panel, textvariable=self.collection_name_var).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        row += 1

        # Reconnect button
        ttk.Button(left_panel, text="Reconnect MongoDB",
                   command=self.connect_mongodb).grid(
            row=row, column=0, columnspan=2, pady=10)
        row += 1

        ttk.Separator(left_panel, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1

        # Serial Settings
        ttk.Label(left_panel, text="Serial Port:").grid(row=row, column=0, sticky=tk.W, pady=5)
        port_combo = ttk.Combobox(left_panel, textvariable=self.port_var,
                                  values=["COM3", "COM4", "COM5", "COM6", "COM7", "COM8"])
        port_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        row += 1

        ttk.Label(left_panel, text="Baud Rate:").grid(row=row, column=0, sticky=tk.W, pady=5)
        baud_combo = ttk.Combobox(left_panel, textvariable=self.baudrate_var,
                                  values=["9600", "115200", "57600", "38400", "19200"])
        baud_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        row += 1

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(left_panel, variable=self.progress_var, maximum=5)
        self.progress_bar.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        row += 1

        # Control Buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        row += 1

        self.start_btn = ttk.Button(button_frame, text="Start Collection",
                                    command=self.start_collection, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(button_frame, text="Stop",
                                   command=self.stop_collection, state=tk.DISABLED, width=15)
        self.stop_btn.pack(side=tk.LEFT)

        # Compare Button
        self.compare_btn = ttk.Button(left_panel, text="Compare with Database",
                                      command=self.compare_with_database, state=tk.DISABLED)
        self.compare_btn.grid(row=row, column=0, columnspan=2, pady=10)
        row += 1

        # Save Results Button
        self.save_btn = ttk.Button(left_panel, text="Save to Database",
                                   command=self.save_to_database, state=tk.DISABLED)
        self.save_btn.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # Add IC Button
        self.add_ic_btn = ttk.Button(left_panel, text="Add New IC to Database",
                                     command=self.add_ic_to_database)
        self.add_ic_btn.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # View Database Button
        self.view_db_btn = ttk.Button(left_panel, text="View Database",
                                      command=self.view_database)
        self.view_db_btn.grid(row=row, column=0, columnspan=2, pady=5)

        # Right panel - Data Display
        right_panel = ttk.LabelFrame(main_frame, text="Data & Results", padding="10")
        right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)

        # Create PanedWindow for split view
        paned_window = ttk.PanedWindow(right_panel, orient=tk.HORIZONTAL)
        paned_window.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)

        # Left side - Notebook
        notebook_frame = ttk.Frame(paned_window)
        paned_window.add(notebook_frame, weight=1)

        # Right side - Photo display
        photo_frame = ttk.LabelFrame(paned_window, text="IC Photo", padding="10")
        paned_window.add(photo_frame, weight=3)

        photo_frame.columnconfigure(0, weight=1)
        photo_frame.rowconfigure(0, weight=1)
        photo_frame.rowconfigure(1, weight=0)

        photo_container = ttk.Frame(photo_frame)
        photo_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        photo_container.columnconfigure(0, weight=1)
        photo_container.rowconfigure(0, weight=1)

        self.photo_label = tk.Label(photo_container, text="No photo available",
                                    relief=tk.SUNKEN, anchor=tk.CENTER,
                                    bg='white', font=("Arial", 12))
        self.photo_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.ic_info_label = ttk.Label(photo_frame, text="",
                                       font=("Arial", 14, "bold"))
        self.ic_info_label.grid(row=1, column=0, pady=5, sticky=tk.W)

        # Notebook for tabs
        notebook = ttk.Notebook(notebook_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Real-time Data
        data_tab = ttk.Frame(notebook)
        notebook.add(data_tab, text="Real-time Data")
        data_tab.columnconfigure(0, weight=1)
        data_tab.rowconfigure(0, weight=1)

        values_frame = ttk.LabelFrame(data_tab, text="Current Values", padding="10")
        values_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        values_frame.columnconfigure(0, weight=1)

        self.value_labels = []
        for i in range(8):
            frame = ttk.Frame(values_frame)
            frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2)
            frame.columnconfigure(1, weight=1)
            ttk.Label(frame, text=f"Value {i + 1}:", width=10).grid(row=0, column=0, sticky=tk.W)
            label = ttk.Label(frame, text="0.000", width=15, relief=tk.SUNKEN, anchor=tk.CENTER)
            label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
            self.value_labels.append(label)

        self.message_label = ttk.Label(values_frame, text="Messages: 0/5")
        self.message_label.grid(row=8, column=0, pady=10)

        # Tab 2: Log
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="Log")
        log_tab.columnconfigure(0, weight=1)
        log_tab.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_tab, height=20)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tab 3: Comparison Results
        results_tab = ttk.Frame(notebook)
        notebook.add(results_tab, text="Comparison Results")
        results_tab.columnconfigure(0, weight=1)
        results_tab.rowconfigure(0, weight=1)

        columns = ("Rank", "IC Name", "SSE", "Similarity (%)")
        self.results_tree = ttk.Treeview(results_tab, columns=columns, show="headings", height=15)

        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "IC Name":
                self.results_tree.column(col, width=200)
            else:
                self.results_tree.column(col, width=100)

        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_selected)

        v_scrollbar = ttk.Scrollbar(results_tab, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_tab, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Tab 4: Visualization
        viz_tab = ttk.Frame(notebook)
        notebook.add(viz_tab, text="Visualization")
        viz_tab.columnconfigure(0, weight=1)
        viz_tab.rowconfigure(0, weight=1)

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(5, 4))
        self.fig.text(0.02, 0.98, 'Group 23', fontsize=10,
                      fontweight='bold', color='blue',
                      verticalalignment='top')
        self.fig.tight_layout(pad=3.0, rect=[0.05, 0.05, 0.95, 0.95])

        self.canvas = FigureCanvasTkAgg(self.fig, viz_tab)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                 relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), ipady=2)

        status_info = tk.Label(status_frame, text="Group 23|Gasser Mohamed|Ahmed Mahfouz|Fares Farrag|Ahmed Hossam|Dr. Hossam El-Din Moustafa",
                               font=("Arial", 9),
                               bg="lightgray",
                               relief=tk.SUNKEN)
        status_info.grid(row=0, column=1, ipadx=10, ipady=2, sticky=tk.E)

    def connect_mongodb(self):
        """Connect to MongoDB"""
        try:
            if self.mongo_client:
                self.mongo_client.close()

            self.update_status("Connecting to MongoDB...")
            self.mongo_client = pymongo.MongoClient(self.mongo_uri_var.get(), serverSelectionTimeoutMS=5000)

            # Test connection
            self.mongo_client.server_info()

            self.db = self.mongo_client[self.db_name_var.get()]
            self.collection = self.db[self.collection_name_var.get()]

            # Create indexes
            self.collection.create_index("ic_name")
            self.collection.create_index("timestamp")

            count = self.collection.count_documents({})
            self.update_status(f"✓ Connected to MongoDB. Database has {count} ICs.")
            messagebox.showinfo("Success",
                                f"Connected to MongoDB!\nDatabase: {self.db_name_var.get()}\nICs in database: {count}")

        except Exception as e:
            self.update_status(f"✗ MongoDB connection failed: {e}")
            messagebox.showerror("MongoDB Error", f"Failed to connect:\n{str(e)}")

    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, message):
        self.status_var.set(message)
        self.log_message(message)

    def update_value_display(self, index, value):
        if index < len(self.value_labels):
            self.value_labels[index].config(text=f"{value:.3f}")

    def update_progress(self, current, total=5):
        self.progress_var.set(current)
        self.message_label.config(text=f"Messages: {current}/{total}")

    def display_ic_photo(self, ic_name):
        """Display the photo of the selected IC from MongoDB"""
        try:
            self.ic_info_label.config(text=f"Loading photo for: {ic_name}...")
            self.root.update()

            # Find IC document in MongoDB
            ic_doc = self.collection.find_one({"ic_name": ic_name})

            if ic_doc and "photo" in ic_doc:
                # Decode base64 image
                image_data = base64.b64decode(ic_doc["photo"])
                image_stream = io.BytesIO(image_data)
                self.current_image = Image.open(image_stream)

                # Get label size
                label_width = self.photo_label.winfo_width()
                label_height = self.photo_label.winfo_height()

                if label_width < 100 or label_height < 100:
                    max_size = (600, 600)
                else:
                    max_size = (label_width - 20, label_height - 20)

                # Resize
                self.current_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                self.current_photo = ImageTk.PhotoImage(self.current_image)

                self.photo_label.config(image=self.current_photo, text="")
                self.ic_info_label.config(text=f"IC: {ic_name}")
                self.update_status(f"Photo loaded for: {ic_name}")
            else:
                self.photo_label.config(image='',
                                        text=f"No photo found for:\n{ic_name}")
                self.ic_info_label.config(text=f"IC: {ic_name} (No Image)")
                self.update_status(f"No photo in database for: {ic_name}")

        except Exception as e:
            self.update_status(f"Error loading photo: {e}")
            self.photo_label.config(image='', text=f"Error loading photo\n{str(e)[:50]}...")

    def on_result_selected(self, event):
        """Handle selection of a result"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            values = item['values']
            if values and len(values) >= 2:
                ic_name = values[1]
                threading.Thread(target=self.display_ic_photo, args=(ic_name,), daemon=True).start()

    def start_collection(self):
        if self.collecting:
            return

        self.collecting = True
        self.messages = []
        self.current_buffer = []
        self.averaged_array = []

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.compare_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)

        for label in self.value_labels:
            label.config(text="0.000")
        self.results_tree.delete(*self.results_tree.get_children())
        self.photo_label.config(image='', text="No photo available")
        self.ic_info_label.config(text="")

        self.collection_thread = threading.Thread(target=self.collect_data, daemon=True)
        self.collection_thread.start()

    def collect_data(self):
        try:
            self.update_status(f"Connecting to {self.port_var.get()}...")

            self.serial_conn = serial.Serial(
                port=self.port_var.get(),
                baudrate=int(self.baudrate_var.get()),
                timeout=1
            )
            time.sleep(2)

            self.update_status("Connected. Reading values...")

            while self.collecting and len(self.messages) < 5:
                if self.serial_conn.in_waiting > 0:
                    raw = self.serial_conn.readline().decode('utf-8').strip()

                    if raw:
                        try:
                            value = float(raw)
                            idx = len(self.current_buffer)

                            self.root.after(0, self.update_value_display, idx, value)
                            self.current_buffer.append(value)

                            if len(self.current_buffer) == 8:
                                self.messages.append(self.current_buffer.copy())
                                current_count = len(self.messages)

                                self.root.after(0, self.update_progress, current_count)
                                self.update_status(f"Message #{current_count} complete")
                                self.current_buffer = []

                                for i in range(8):
                                    self.root.after(0, self.update_value_display, i, 0.0)

                        except ValueError:
                            self.update_status(f"Invalid value: {raw}")

            if len(self.messages) == 5:
                self.compute_average()
                self.update_status("Data collection complete!")
                self.root.after(0, self.enable_compare_button)

        except Exception as e:
            self.update_status(f"Error: {e}")
            messagebox.showerror("Error", str(e))

        finally:
            self.stop_collection()

    def compute_average(self):
        """Compute averaged array"""
        A = []
        for col in range(8):
            col_values = [msg[col] for msg in self.messages]
            avg_val = sum(col_values) / len(col_values)
            A.append(avg_val)

        self.averaged_array = A
        self.update_status(f"Averaged array: {[f'{v:.3f}' for v in A]}")
        self.update_visualization()

    def enable_compare_button(self):
        self.compare_btn.config(state=tk.NORMAL)

    def stop_collection(self):
        self.collecting = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        if self.serial_conn and hasattr(self.serial_conn, 'is_open') and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                self.update_status("Serial closed")
            except Exception as e:
                self.update_status(f"Error closing serial: {e}")

        self.serial_conn = None

    def compare_with_database(self):
        """Compare measured data with all ICs in MongoDB"""
        if not self.averaged_array:
            messagebox.showwarning("No Data", "Collect data first.")
            return

        try:
            self.update_status("Comparing with database...")

            # Get all ICs from database
            all_ics = list(self.collection.find({"readings": {"$exists": True}}))

            if not all_ics:
                messagebox.showwarning("Empty Database", "No ICs in database to compare.")
                return

            results = []

            for ic_doc in all_ics:
                ic_name = ic_doc.get("ic_name", "Unknown")
                ic_readings = ic_doc.get("readings", [])

                if len(ic_readings) == 8:
                    # Calculate SSE
                    sse = sum((a - b) ** 2 for a, b in zip(self.averaged_array, ic_readings))
                    results.append((ic_name, sse, ic_readings))

            # Sort by SSE
            results.sort(key=lambda x: x[1])
            self.comparison_results = results

            # Clear tree
            self.results_tree.delete(*self.results_tree.get_children())

            # Add to treeview
            for i, (name, sse, data) in enumerate(results, 1):
                similarity = 100 / (1 + sse) if sse > 0 else 100
                self.results_tree.insert("", tk.END, values=(
                    i, name, f"{sse:.4f}", f"{similarity:.1f}%"
                ))

            if results:
                best_name, best_sse, _ = results[0]
                self.update_status(f"Best match: {best_name} (SSE: {best_sse:.4f})")

                # Select best match
                first_item = self.results_tree.get_children()[0]
                self.results_tree.selection_set(first_item)
                self.results_tree.focus(first_item)

                # Show photo
                threading.Thread(target=self.display_ic_photo, args=(best_name,), daemon=True).start()

            self.save_btn.config(state=tk.NORMAL)

        except Exception as e:
            self.update_status(f"Comparison error: {e}")
            messagebox.showerror("Error", str(e))

    def save_to_database(self):
        """Save measurement results to database"""
        if not self.averaged_array:
            messagebox.showwarning("No Data", "No data to save.")
            return

        # Ask for IC name
        ic_name = tk.simpledialog.askstring("Save to Database",
                                            "Enter IC name for this measurement:")

        if not ic_name:
            return

        try:
            # Check if already exists
            existing = self.collection.find_one({"ic_name": ic_name})

            doc = {
                "ic_name": ic_name,
                "readings": self.averaged_array,
                "timestamp": datetime.now(),
                "messages": self.messages,
                "comparison_results": [
                    {"name": name, "sse": sse}
                    for name, sse, _ in self.comparison_results[:5]
                ] if self.comparison_results else []
            }

            if existing:
                # Update
                self.collection.update_one(
                    {"ic_name": ic_name},
                    {"$set": doc}
                )
                self.update_status(f"Updated IC: {ic_name}")
                messagebox.showinfo("Success", f"Updated IC in database:\n{ic_name}")
            else:
                # Insert
                self.collection.insert_one(doc)
                self.update_status(f"Added IC: {ic_name}")
                messagebox.showinfo("Success", f"Added new IC to database:\n{ic_name}")

        except Exception as e:
            self.update_status(f"Save error: {e}")
            messagebox.showerror("Error", str(e))

    def add_ic_to_database(self):
        """Add a new IC with manual data and photo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New IC")
        dialog.geometry("500x600")

        ttk.Label(dialog, text="IC Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Readings (8 values, comma-separated):").grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)

        readings_text = tk.Text(dialog, height=3, width=50)
        readings_text.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        readings_text.insert("1.0", "0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0")

        photo_path_var = tk.StringVar()
        ttk.Label(dialog, text="Photo (optional):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        ttk.Entry(dialog, textvariable=photo_path_var, width=30).grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)

        def browse_photo():
            filename = filedialog.askopenfilename(
                title="Select IC Photo",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
            )
            if filename:
                photo_path_var.set(filename)

        ttk.Button(dialog, text="Browse", command=browse_photo).grid(row=3, column=1, padx=10, pady=10, sticky=tk.E)

        def save_ic():
            try:
                ic_name = name_entry.get().strip()
                if not ic_name:
                    messagebox.showerror("Error", "IC name required")
                    return

                # Parse readings
                readings_str = readings_text.get("1.0", tk.END).strip()
                readings = [float(x.strip()) for x in readings_str.split(",")]

                if len(readings) != 8:
                    messagebox.showerror("Error", "Must provide exactly 8 readings")
                    return

                doc = {
                    "ic_name": ic_name,
                    "readings": readings,
                    "timestamp": datetime.now(),
                    "added_manually": True
                }

                # Add photo if provided
                photo_path = photo_path_var.get()
                if photo_path and os.path.exists(photo_path):
                    with open(photo_path, "rb") as f:
                        photo_data = f.read()
                        doc["photo"] = base64.b64encode(photo_data).decode('utf-8')

                # Insert or update
                existing = self.collection.find_one({"ic_name": ic_name})
                if existing:
                    self.collection.update_one({"ic_name": ic_name}, {"$set": doc})
                    messagebox.showinfo("Success", f"Updated IC: {ic_name}")
                else:
                    self.collection.insert_one(doc)
                    messagebox.showinfo("Success", f"Added IC: {ic_name}")

                dialog.destroy()
                self.update_status(f"IC added: {ic_name}")

            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Save IC", command=save_ic).grid(
            row=4, column=0, columnspan=2, pady=20)

    def view_database(self):
        """View all ICs in database"""
        try:
            all_ics = list(self.collection.find())

            if not all_ics:
                messagebox.showinfo("Database", "Database is empty")
                return

            # Create view window
            view_window = tk.Toplevel(self.root)
            view_window.title("Database Viewer")
            view_window.geometry("800x600")

            # Create treeview
            columns = ("IC Name", "Readings", "Timestamp", "Has Photo")
            tree = ttk.Treeview(view_window, columns=columns, show="headings")

            for col in columns:
                tree.heading(col, text=col)
                if col == "IC Name":
                    tree.column(col, width=200)
                elif col == "Readings":
                    tree.column(col, width=300)
                else:
                    tree.column(col, width=150)

            # Add data
            for ic in all_ics:
                name = ic.get("ic_name", "Unknown")
                readings = ic.get("readings", [])
                readings_str = ", ".join([f"{r:.2f}" for r in readings]) if readings else "N/A"
                timestamp = ic.get("timestamp", "N/A")
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
                has_photo = "Yes" if "photo" in ic else "No"

                tree.insert("", tk.END, values=(name, readings_str, timestamp, has_photo))

            # Scrollbars
            vsb = ttk.Scrollbar(view_window, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(view_window, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
            vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
            hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))

            view_window.columnconfigure(0, weight=1)
            view_window.rowconfigure(0, weight=1)

            # Delete button
            def delete_selected():
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    ic_name = item['values'][0]
                    if messagebox.askyesno("Confirm Delete", f"Delete IC: {ic_name}?"):
                        self.collection.delete_one({"ic_name": ic_name})
                        tree.delete(selection[0])
                        self.update_status(f"Deleted IC: {ic_name}")

            ttk.Button(view_window, text="Delete Selected", command=delete_selected).grid(
                row=2, column=0, columnspan=2, pady=10)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_visualization(self):
        """Update matplotlib visualization"""
        self.ax1.clear()
        self.ax2.clear()

        if self.messages:
            messages_array = np.array(self.messages)
            for i, message in enumerate(messages_array):
                self.ax1.plot(range(1, 9), message, 'o-', label=f'Message {i + 1}', alpha=0.7)

            if self.averaged_array:
                self.ax1.plot(range(1, 9), self.averaged_array, 'ko-',
                              linewidth=3, markersize=8, label='Average')

            self.ax1.set_xlabel('Value Index')
            self.ax1.set_ylabel('Value')
            self.ax1.set_title('All Messages with Average')
            self.ax1.legend()
            self.ax1.grid(True, alpha=0.3)

        if self.averaged_array and self.comparison_results:
            self.ax2.plot(range(1, 9), self.averaged_array, 'bo-',
                          linewidth=2, markersize=6, label='Measured')

            name, sse, best_data = self.comparison_results[0]
            self.ax2.plot(range(1, 9), best_data, 'ro-',
                          linewidth=2, markersize=6, label=f'Best: {name}')

            self.ax2.set_xlabel('Value Index')
            self.ax2.set_ylabel('Value')
            self.ax2.set_title(f'Measured vs Best Match (SSE: {sse:.4f})')
            self.ax2.legend()
            self.ax2.grid(True, alpha=0.3)

        self.canvas.draw()

    def on_closing(self):
        """Clean up on window close"""
        self.stop_collection()
        if self.mongo_client:
            self.mongo_client.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MongoDBICTesterGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    import tkinter.simpledialog

    main()

