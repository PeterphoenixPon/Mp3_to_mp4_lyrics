#!/usr/bin/env python3
"""
Independent GUI for MP3 to MP4 Lyrics Video Converter
Provides a user-friendly interface for the lyrics_video_converter_tunable.py script
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import sys
import os
import threading
from pathlib import Path
import queue

# Fix encoding issues on Windows
if sys.platform == 'win32':
    import locale
    # Set console output to UTF-8
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    # Set environment variable for subprocess
    os.environ['PYTHONIOENCODING'] = 'utf-8'


class LyricsVideoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lyrics Video Converter")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Queue for thread-safe communication
        self.output_queue = queue.Queue()
        
        # Variables
        self.audio_path = tk.StringVar()
        self.lyrics_path = tk.StringVar()
        self.output_path = tk.StringVar()
        
        # Model selection
        self.model_var = tk.StringVar(value="base")
        
        # Color options
        self.bg_color_var = tk.StringVar(value="black")
        self.text_color_var = tk.StringVar(value="white")
        
        # Metadata
        self.title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.album_var = tk.StringVar()
        
        # Processing options
        self.lrc_only_var = tk.BooleanVar(value=False)
        self.skip_video_var = tk.BooleanVar(value=False)
        self.use_cpu_var = tk.BooleanVar(value=False)
        self.debug_var = tk.BooleanVar(value=False)
        
        # Advanced parameters
        self.match_threshold_var = tk.IntVar(value=55)
        self.search_window_var = tk.IntVar(value=40)
        self.anchor_interval_var = tk.IntVar(value=2)
        self.overlap_weight_var = tk.DoubleVar(value=0.4)
        self.global_offset_var = tk.DoubleVar(value=0.0)
        self.speed_multiplier_var = tk.DoubleVar(value=1.0)
        self.empty_line_gap_var = tk.DoubleVar(value=0.1)
        self.section_header_gap_var = tk.DoubleVar(value=0.1)
        self.min_line_spacing_var = tk.DoubleVar(value=3.0)
        self.start_offset_var = tk.DoubleVar(value=3.0)
        self.end_offset_var = tk.DoubleVar(value=3.0)
        
        self.create_widgets()
        self.check_output_queue()
        
    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)  # Left side (tabs) gets more space
        main_frame.columnconfigure(1, weight=2)  # Right side (console) gets less space
        main_frame.rowconfigure(0, weight=1)
        
        # Left frame for tabs and buttons
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(left_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Tab 1: Basic Settings
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Basic Settings")
        self.create_basic_settings(basic_frame)
        
        # Tab 2: Advanced Parameters
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="Advanced Parameters")
        self.create_advanced_settings(advanced_frame)
        
        # Tab 3: Metadata
        metadata_frame = ttk.Frame(notebook, padding="10")
        notebook.add(metadata_frame, text="Metadata")
        self.create_metadata_settings(metadata_frame)
        
        # Control buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(button_frame, text="Process", command=self.process, 
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_defaults, 
                  width=20).pack(side=tk.LEFT, padx=5)
        
        # Right frame for console
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Output console
        console_label = ttk.Label(right_frame, text="Console Output:")
        console_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.console = scrolledtext.ScrolledText(right_frame, width=50, 
                                                 state='disabled', wrap=tk.WORD)
        self.console.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Progress bar at bottom of console
        self.progress = ttk.Progressbar(right_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
    def create_basic_settings(self, parent):
        # File Selection Section
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="10")
        file_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Audio file
        ttk.Label(file_frame, text="Audio File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.audio_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_audio).grid(row=0, column=2, pady=5)
        
        # Lyrics file
        ttk.Label(file_frame, text="Lyrics File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.lyrics_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_lyrics).grid(row=1, column=2, pady=5)
        
        # Output file
        ttk.Label(file_frame, text="Output File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_path, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_output).grid(row=2, column=2, pady=5)
        
        # Model Selection
        model_frame = ttk.LabelFrame(parent, text="Whisper Model", padding="10")
        model_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(model_frame, text="Select Model:").grid(row=0, column=0, sticky=tk.W, padx=5)
        models = ['tiny', 'base', 'small', 'medium', 'large']
        model_menu = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                  values=models, state='readonly', width=15)
        model_menu.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(model_frame, text="(larger = more accurate, slower)", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Visual Settings
        visual_frame = ttk.LabelFrame(parent, text="Visual Settings", padding="10")
        visual_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Background color
        ttk.Label(visual_frame, text="Background Color:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        bg_colors = ['black', 'white', 'blue', 'red', 'green', 'gray']
        ttk.Combobox(visual_frame, textvariable=self.bg_color_var, 
                    values=bg_colors, state='readonly', width=15).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Text color
        ttk.Label(visual_frame, text="Text Color:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        text_colors = ['white', 'yellow', 'cyan', 'green', 'magenta', 'red', 'blue']
        ttk.Combobox(visual_frame, textvariable=self.text_color_var, 
                    values=text_colors, state='readonly', width=15).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Processing Options
        options_frame = ttk.LabelFrame(parent, text="Processing Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(options_frame, text="✓ LRC file is always generated", 
                 foreground="green").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Checkbutton(options_frame, text="Skip video creation (generate LRC only)", 
                       variable=self.skip_video_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Checkbutton(options_frame, text="Use CPU instead of GPU", 
                       variable=self.use_cpu_var).grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Checkbutton(options_frame, text="Debug mode (verbose output)", 
                       variable=self.debug_var).grid(row=3, column=0, sticky=tk.W, padx=5, pady=3)
        
    def create_advanced_settings(self, parent):
        # Create a canvas with scrollbar for advanced settings
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Matching Quality
        match_frame = ttk.LabelFrame(scrollable_frame, text="Matching Quality", padding="10")
        match_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(match_frame, text="Match Threshold (40-80):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(match_frame, from_=40, to=80, variable=self.match_threshold_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(match_frame, textvariable=self.match_threshold_var).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(match_frame, text="Lower = more matches, Higher = more accurate", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        # Search Window
        ttk.Label(match_frame, text="Search Window (20-50s):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Scale(match_frame, from_=20, to=50, variable=self.search_window_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(match_frame, textvariable=self.search_window_var).grid(row=2, column=2, padx=5, pady=5)
        
        # Anchor Settings
        anchor_frame = ttk.LabelFrame(scrollable_frame, text="Anchor Settings", padding="10")
        anchor_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(anchor_frame, text="Anchor Check Interval (2-5):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(anchor_frame, from_=2, to=5, variable=self.anchor_interval_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(anchor_frame, textvariable=self.anchor_interval_var).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(anchor_frame, text="Overlap Weight (0.2-0.6):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(anchor_frame, from_=0.2, to=0.6, variable=self.overlap_weight_var, 
                 orient=tk.HORIZONTAL, length=200, command=lambda v: self.overlap_weight_var.set(round(float(v), 1))).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(anchor_frame, textvariable=self.overlap_weight_var).grid(row=1, column=2, padx=5, pady=5)
        
        # Timing Adjustments
        timing_frame = ttk.LabelFrame(scrollable_frame, text="Timing Adjustments", padding="10")
        timing_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(timing_frame, text="Global Time Offset (-3.0 to +3.0s):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(timing_frame, from_=-3.0, to=3.0, variable=self.global_offset_var, 
                 orient=tk.HORIZONTAL, length=200, command=lambda v: self.global_offset_var.set(round(float(v), 1))).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(timing_frame, textvariable=self.global_offset_var).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(timing_frame, text="Speed Multiplier (0.9-1.1):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(timing_frame, from_=0.9, to=1.1, variable=self.speed_multiplier_var, 
                 orient=tk.HORIZONTAL, length=200, command=lambda v: self.speed_multiplier_var.set(round(float(v), 2))).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(timing_frame, textvariable=self.speed_multiplier_var).grid(row=1, column=2, padx=5, pady=5)
        
        # Spacing Settings
        spacing_frame = ttk.LabelFrame(scrollable_frame, text="Spacing Settings", padding="10")
        spacing_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(spacing_frame, text="Empty Line Gap (0.0-2.0s):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(spacing_frame, from_=0.0, to=2.0, variable=self.empty_line_gap_var, 
                 orient=tk.HORIZONTAL, length=200, command=lambda v: self.empty_line_gap_var.set(round(float(v), 1))).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(spacing_frame, textvariable=self.empty_line_gap_var).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(spacing_frame, text="Section Header Gap (0.0-3.0s):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(spacing_frame, from_=0.0, to=3.0, variable=self.section_header_gap_var, 
                 orient=tk.HORIZONTAL, length=200, command=lambda v: self.section_header_gap_var.set(round(float(v), 1))).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(spacing_frame, textvariable=self.section_header_gap_var).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(spacing_frame, text="Min Line Spacing (0.5-5.0s):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Scale(spacing_frame, from_=0.5, to=5.0, variable=self.min_line_spacing_var, 
                 orient=tk.HORIZONTAL, length=200, command=lambda v: self.min_line_spacing_var.set(round(float(v), 1))).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(spacing_frame, textvariable=self.min_line_spacing_var).grid(row=2, column=2, padx=5, pady=5)
        
        # Boundary Settings
        boundary_frame = ttk.LabelFrame(scrollable_frame, text="Boundary Offsets", padding="10")
        boundary_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(boundary_frame, text="Start Offset (0.0-10.0s):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(boundary_frame, from_=0.0, to=10.0, variable=self.start_offset_var, 
                 orient=tk.HORIZONTAL, length=200, command=lambda v: self.start_offset_var.set(round(float(v), 1))).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(boundary_frame, textvariable=self.start_offset_var).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(boundary_frame, text="End Offset (0.0-10.0s):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(boundary_frame, from_=0.0, to=10.0, variable=self.end_offset_var, 
                 orient=tk.HORIZONTAL, length=200, command=lambda v: self.end_offset_var.set(round(float(v), 1))).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(boundary_frame, textvariable=self.end_offset_var).grid(row=1, column=2, padx=5, pady=5)
        
    def create_metadata_settings(self, parent):
        metadata_frame = ttk.LabelFrame(parent, text="Song Metadata (Optional)", padding="10")
        metadata_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(metadata_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(metadata_frame, textvariable=self.title_var, width=40).grid(row=0, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))
        
        ttk.Label(metadata_frame, text="Artist:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(metadata_frame, textvariable=self.artist_var, width=40).grid(row=1, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))
        
        ttk.Label(metadata_frame, text="Album:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(metadata_frame, textvariable=self.album_var, width=40).grid(row=2, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))
        
        metadata_frame.columnconfigure(1, weight=1)
        
    def browse_audio(self):
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.flac"), ("All Files", "*.*")]
        )
        if filename:
            self.audio_path.set(filename)
            # Auto-set output path if not already set
            if not self.output_path.get():
                stem = Path(filename).stem
                output = str(Path(filename).parent / f"{stem}_with_lyrics.mp4")
                self.output_path.set(output)
    
    def browse_lyrics(self):
        filename = filedialog.askopenfilename(
            title="Select Lyrics File",
            filetypes=[("Text Files", "*.txt *.lrc"), ("All Files", "*.*")]
        )
        if filename:
            self.lyrics_path.set(filename)
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save Video As",
            defaultextension=".mp4",
            filetypes=[("MP4 Files", "*.mp4"), ("All Files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def reset_defaults(self):
        """Reset all parameters to default values"""
        self.match_threshold_var.set(55)
        self.search_window_var.set(40)
        self.anchor_interval_var.set(2)
        self.overlap_weight_var.set(0.4)
        self.global_offset_var.set(0.0)
        self.speed_multiplier_var.set(1.0)
        self.empty_line_gap_var.set(0.1)
        self.section_header_gap_var.set(0.1)
        self.min_line_spacing_var.set(3.0)
        self.start_offset_var.set(3.0)
        self.end_offset_var.set(3.0)
        self.model_var.set("base")
        self.bg_color_var.set("black")
        self.text_color_var.set("white")
        self.skip_video_var.set(False)
        self.use_cpu_var.set(False)
        self.debug_var.set(False)
        self.log_message("Parameters reset to defaults")
    
    def log_message(self, message):
        """Add a message to the console"""
        self.console.config(state='normal')
        self.console.insert(tk.END, message + '\n')
        self.console.see(tk.END)
        self.console.config(state='disabled')
    
    def check_output_queue(self):
        """Check for messages from the processing thread"""
        try:
            while True:
                message = self.output_queue.get_nowait()
                if message == "DONE":
                    self.progress.stop()
                    self.log_message("\n✓ Processing complete!")
                    messagebox.showinfo("Success", "Video processing completed successfully!")
                elif message == "ERROR":
                    self.progress.stop()
                    self.log_message("\n❌ Processing failed!")
                    messagebox.showerror("Error", "Processing failed. Check console for details.")
                else:
                    self.log_message(message)
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_output_queue)
    
    def build_command(self):
        """Build the command line for the script"""
        # Find the script file
        script_name = "lyrics_video_converter_tunable.py"
        
        # Check multiple possible locations
        possible_paths = [
            script_name,  # Current directory
            os.path.join(os.path.dirname(__file__), script_name),  # Same dir as GUI
            os.path.join(os.getcwd(), script_name),  # Working directory
        ]
        
        script_path = None
        for path in possible_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            raise FileNotFoundError(
                f"Cannot find {script_name}. Please ensure it's in the same directory as this GUI script."
            )
        
        # Build command as list - Python handles quoting automatically
        cmd = [sys.executable, script_path]
        
        # Required arguments - paths are kept as separate list items
        cmd.append(self.audio_path.get())
        cmd.append(self.lyrics_path.get())
        
        # Optional output
        if self.output_path.get():
            cmd.append('-o')
            cmd.append(self.output_path.get())
        
        # Model
        cmd.append('-m')
        cmd.append(self.model_var.get())
        
        # Colors
        cmd.append('--bg-color')
        cmd.append(self.bg_color_var.get())
        cmd.append('--text-color')
        cmd.append(self.text_color_var.get())
        
        # Metadata
        if self.title_var.get():
            cmd.append('--title')
            cmd.append(self.title_var.get())
        if self.artist_var.get():
            cmd.append('--artist')
            cmd.append(self.artist_var.get())
        if self.album_var.get():
            cmd.append('--album')
            cmd.append(self.album_var.get())
        
        # Options
        if self.skip_video_var.get():
            cmd.append('--lrc-only')
        if self.use_cpu_var.get():
            cmd.append('--cpu')
        if self.debug_var.get():
            cmd.append('--debug')
        
        # Advanced parameters (only if not default)
        if self.match_threshold_var.get() != 55:
            cmd.append('--threshold')
            cmd.append(str(self.match_threshold_var.get()))
        if self.global_offset_var.get() != 0.0:
            cmd.append('--offset')
            cmd.append(str(self.global_offset_var.get()))
        if self.speed_multiplier_var.get() != 1.0:
            cmd.append('--speed')
            cmd.append(str(self.speed_multiplier_var.get()))
        
        return cmd
    
    def process_thread(self, cmd):
        """Run the processing in a separate thread"""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'  # Replace problematic characters instead of crashing
            )
            
            # Read output line by line
            for line in process.stdout:
                self.output_queue.put(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                self.output_queue.put("DONE")
            else:
                self.output_queue.put("ERROR")
                
        except Exception as e:
            self.output_queue.put(f"Error: {str(e)}")
            self.output_queue.put("ERROR")
    
    def process(self):
        """Start the processing"""
        # Validate inputs
        if not self.audio_path.get():
            messagebox.showerror("Error", "Please select an audio file")
            return
        
        if not self.lyrics_path.get():
            messagebox.showerror("Error", "Please select a lyrics file")
            return
        
        if not os.path.exists(self.audio_path.get()):
            messagebox.showerror("Error", "Audio file does not exist")
            return
        
        if not os.path.exists(self.lyrics_path.get()):
            messagebox.showerror("Error", "Lyrics file does not exist")
            return
        
        # Clear console
        self.console.config(state='normal')
        self.console.delete(1.0, tk.END)
        self.console.config(state='disabled')
        
        # Build command
        try:
            cmd = self.build_command()
            # Display command with proper quoting for readability
            import shlex
            cmd_display = ' '.join(shlex.quote(arg) for arg in cmd)
            self.log_message(f"Command: {cmd_display}\n")
            self.log_message("="*60)
            self.log_message("Starting processing...")
            self.log_message("="*60 + "\n")
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to build command: {str(e)}")
            return
        
        # Start progress bar
        self.progress.start()
        
        # Start processing in a thread
        thread = threading.Thread(target=self.process_thread, args=(cmd,), daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = LyricsVideoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()