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
        self.background_image_path = tk.StringVar()
        self.album_art_path = tk.StringVar()
        
        # Model selection
        self.model_var = tk.StringVar(value="base")
        
        # Color options
        self.bg_color_var = tk.StringVar(value="black")
        self.text_color_var = tk.StringVar(value="white")
        
        # Video style
        self.video_style_var = tk.StringVar(value="simple")  # simple or bilibili
        
        # Metadata
        self.title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.album_var = tk.StringVar()
        
        # Processing options
        self.lrc_only_var = tk.BooleanVar(value=False)
        self.skip_video_var = tk.BooleanVar(value=False)
        self.use_cpu_var = tk.BooleanVar(value=False)
        self.debug_var = tk.BooleanVar(value=False)
        
        # Equalizer options
        self.enable_equalizer_var = tk.BooleanVar(value=False)
        self.equalizer_position_var = tk.StringVar(value="bottom")
        self.equalizer_size_var = tk.IntVar(value=200)
        self.equalizer_color_var = tk.StringVar(value="white")
        self.equalizer_bars_var = tk.IntVar(value=20)
        
        # GPU acceleration for effects
        self.use_gpu_encoding_var = tk.BooleanVar(value=True)
        
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
        
        # Tab 2: Visual Effects
        visual_frame = ttk.Frame(notebook, padding="10")
        notebook.add(visual_frame, text="Visual Effects")
        self.create_visual_effects(visual_frame)
        
        # Tab 3: Advanced Parameters
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="Advanced Parameters")
        self.create_advanced_settings(advanced_frame)
        
        # Tab 4: Metadata
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
        
        # Text color
        ttk.Label(visual_frame, text="Text Color:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        text_colors = ['white', 'yellow', 'cyan', 'green', 'magenta', 'red', 'blue']
        ttk.Combobox(visual_frame, textvariable=self.text_color_var, 
                    values=text_colors, state='readonly', width=15).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
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
        
    def create_visual_effects(self, parent):
        # Create a canvas with scrollbar for visual effects settings
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
        
        # Video Style Selection
        style_frame = ttk.LabelFrame(scrollable_frame, text="Video Style", padding="10")
        style_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Radiobutton(style_frame, text="Simple Style (basic background + lyrics)", 
                       variable=self.video_style_var, value="simple").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Radiobutton(style_frame, text="Bilibili Style (album art + waveform + styled layout)", 
                       variable=self.video_style_var, value="bilibili").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        
        # Album Art (for Bilibili style)
        art_frame = ttk.LabelFrame(scrollable_frame, text="Album Artwork (Bilibili Style)", padding="10")
        art_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(art_frame, text="Album Art:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(art_frame, textvariable=self.album_art_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(art_frame, text="Browse...", command=self.browse_album_art).grid(row=0, column=2, pady=5)
        ttk.Label(art_frame, text="(Shows on left side in Bilibili style)", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Background Settings (for Simple style)
        bg_frame = ttk.LabelFrame(scrollable_frame, text="Background (Simple Style)", padding="10")
        bg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Background image
        ttk.Label(bg_frame, text="Background Image:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(bg_frame, textvariable=self.background_image_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(bg_frame, text="Browse...", command=self.browse_background).grid(row=0, column=2, pady=5)
        ttk.Label(bg_frame, text="(Leave empty for solid color)", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Background color (used if no image)
        ttk.Label(bg_frame, text="Background Color:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        bg_colors = ['black', 'white', 'blue', 'red', 'green', 'gray', 'purple', 'navy']
        ttk.Combobox(bg_frame, textvariable=self.bg_color_var, 
                    values=bg_colors, state='readonly', width=15).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(bg_frame, text="(Used if no background image)", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Waveform/Visualizer Settings
        eq_frame = ttk.LabelFrame(scrollable_frame, text="Audio Waveform Visualizer", padding="10")
        eq_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Enable visualizer
        ttk.Checkbutton(eq_frame, text="Show Audio Waveform", 
                       variable=self.enable_equalizer_var).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        ttk.Label(eq_frame, text="(Bilibili style: center-bottom, Simple style: adjustable)", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Separator(eq_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Position
        ttk.Label(eq_frame, text="Position:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        positions = ['bottom', 'top', 'center']
        ttk.Combobox(eq_frame, textvariable=self.equalizer_position_var, 
                    values=positions, state='readonly', width=15).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Size (height)
        ttk.Label(eq_frame, text="Height (50-400px):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Scale(eq_frame, from_=50, to=400, variable=self.equalizer_size_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=3, column=1, padx=5, pady=5)
        ttk.Label(eq_frame, textvariable=self.equalizer_size_var).grid(row=3, column=2, padx=5, pady=5)
        
        # Number of bars
        ttk.Label(eq_frame, text="Number of Bars (10-40):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Scale(eq_frame, from_=10, to=40, variable=self.equalizer_bars_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=4, column=1, padx=5, pady=5)
        ttk.Label(eq_frame, textvariable=self.equalizer_bars_var).grid(row=4, column=2, padx=5, pady=5)
        
        # Color
        ttk.Label(eq_frame, text="Equalizer Color:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        eq_colors = ['white', 'red', 'blue', 'green', 'yellow', 'cyan', 'magenta', 'orange', 'purple']
        ttk.Combobox(eq_frame, textvariable=self.equalizer_color_var, 
                    values=eq_colors, state='readonly', width=15).grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Performance Settings
        perf_frame = ttk.LabelFrame(scrollable_frame, text="Performance", padding="10")
        perf_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Checkbutton(perf_frame, text="Use GPU acceleration for video encoding (NVIDIA only)", 
                       variable=self.use_gpu_encoding_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(perf_frame, text="Speeds up video rendering significantly if you have an NVIDIA GPU", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
    
    def browse_background(self):
        filename = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All Files", "*.*")]
        )
        if filename:
            self.background_image_path.set(filename)
    
    def browse_album_art(self):
        filename = filedialog.askopenfilename(
            title="Select Album Artwork",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All Files", "*.*")]
        )
        if filename:
            self.album_art_path.set(filename)
    
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
        self.background_image_path.set("")
        self.album_art_path.set("")
        self.video_style_var.set("simple")
        self.skip_video_var.set(False)
        self.use_cpu_var.set(False)
        self.debug_var.set(False)
        self.enable_equalizer_var.set(False)
        self.equalizer_position_var.set("bottom")
        self.equalizer_size_var.set(200)
        self.equalizer_color_var.set("white")
        self.equalizer_bars_var.set(20)
        self.use_gpu_encoding_var.set(True)
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
        # If visual effects are enabled, only generate LRC with main script
        # The wrapper will create the final video
        if (self.video_style_var.get() == 'bilibili' or 
            self.background_image_path.get() or 
            self.enable_equalizer_var.get()) and not self.skip_video_var.get():
            cmd.append('--lrc-only')
        elif self.skip_video_var.get():
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
    
    def build_wrapper_command(self):
        """Build command for the wrapper script that adds visual effects"""
        import json
        
        # Choose wrapper script based on style
        if self.video_style_var.get() == 'bilibili':
            wrapper_script = "lyrics_video_bilibili.py"
        else:
            wrapper_script = "lyrics_video_wrapper.py"
        
        # Check for wrapper script
        possible_paths = [
            wrapper_script,
            os.path.join(os.path.dirname(__file__), wrapper_script),
            os.path.join(os.getcwd(), wrapper_script),
        ]
        
        wrapper_path = None
        for path in possible_paths:
            if os.path.exists(path):
                wrapper_path = path
                break
        
        if not wrapper_path:
            raise FileNotFoundError(
                f"Cannot find {wrapper_script}. Please ensure it's in the same directory as the GUI."
            )
        
        # Determine LRC path
        audio_stem = Path(self.audio_path.get()).stem
        lrc_path = f"{audio_stem}_synced.lrc"
        
        # Build command
        cmd = [sys.executable, wrapper_path]
        cmd.append(self.audio_path.get())
        cmd.append(lrc_path)
        
        # Output path
        if self.output_path.get():
            cmd.append(self.output_path.get())
        else:
            cmd.append(f"{audio_stem}_with_lyrics.mp4")
        
        # Colors
        cmd.append('--bg-color')
        if self.video_style_var.get() == 'bilibili':
            cmd.append('#1a3b5c')  # Bilibili blue
        else:
            cmd.append(self.bg_color_var.get())
        
        cmd.append('--text-color')
        cmd.append(self.text_color_var.get())
        
        # Bilibili style specific options
        if self.video_style_var.get() == 'bilibili':
            # Album art
            if self.album_art_path.get():
                cmd.append('--album-art')
                cmd.append(self.album_art_path.get())
            
            # Title and artist
            if self.title_var.get():
                cmd.append('--title')
                cmd.append(self.title_var.get())
            if self.artist_var.get():
                cmd.append('--artist')
                cmd.append(self.artist_var.get())
            
            # Waveform config for Bilibili style
            if self.enable_equalizer_var.get():
                wave_config = {
                    'enabled': True,
                    'size': self.equalizer_size_var.get(),
                    'color': self.equalizer_color_var.get()
                }
                cmd.append('--waveform')
                cmd.append(json.dumps(wave_config))
        else:
            # Simple style - background image and equalizer
            if self.background_image_path.get():
                cmd.append('--bg-image')
                cmd.append(self.background_image_path.get())
            
            # Equalizer config for simple style
            if self.enable_equalizer_var.get():
                eq_config = {
                    'enabled': True,
                    'position': self.equalizer_position_var.get(),
                    'size': self.equalizer_size_var.get(),
                    'color': self.equalizer_color_var.get(),
                    'bars': self.equalizer_bars_var.get()
                }
                cmd.append('--equalizer')
                cmd.append(json.dumps(eq_config))
        
        # GPU encoding preference
        if not self.use_gpu_encoding_var.get():
            cmd.append('--no-gpu-encoding')
        
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
            
            if process.returncode != 0:
                self.output_queue.put("ERROR")
                return
            
            # If effects are enabled and we're not in LRC-only mode, create video with effects
            if not self.skip_video_var.get() and (self.video_style_var.get() == 'bilibili' or 
                                                   self.background_image_path.get() or 
                                                   self.enable_equalizer_var.get()):
                self.output_queue.put("\n" + "="*60)
                if self.video_style_var.get() == 'bilibili':
                    self.output_queue.put("Creating Bilibili-style video...")
                else:
                    self.output_queue.put("Applying visual effects...")
                self.output_queue.put("="*60 + "\n")
                
                # Build wrapper command
                wrapper_cmd = self.build_wrapper_command()
                
                wrapper_process = subprocess.Popen(
                    wrapper_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                for line in wrapper_process.stdout:
                    self.output_queue.put(line.rstrip())
                
                wrapper_process.wait()
                
                if wrapper_process.returncode != 0:
                    self.output_queue.put("ERROR")
                    return
            
            self.output_queue.put("DONE")
                
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