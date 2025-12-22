# Lyrics Video Converter GUI

An independent graphical user interface (GUI) for the `lyrics_video_converter_tunable.py` script with additional visual effects support.

## Features

- **User-friendly interface** - No command-line knowledge required
- **All parameters accessible** - Configure every aspect of the conversion
- **Visual effects support** - Add background images and audio equalizers
- **Real-time console output** - See progress as it happens
- **Four organized tabs**:
  - Basic Settings: File selection, model, colors, and basic options
  - Visual Effects: Background images and audio equalizer
  - Advanced Parameters: Fine-tune alignment, timing, and spacing
  - Metadata: Add song title, artist, and album information

## Installation

1. Ensure you have Python 3.7+ installed
2. Place these files in the same directory:
   - `lyrics_video_converter_tunable.py` (script to add existing lyrics to mp4)
   - `lyrics_video_gui.py` (Run this GUI)
   - `lyrics_video_wrapper.py` (handles visual effects)

3. Install required packages (if not already installed):
   ```bash
   pip install torch openai-whisper fuzzywuzzy python-Levenshtein
   ```

## Usage

### Starting the GUI

Run the GUI with:
```bash
python lyrics_video_gui.py
```

Or on Windows, you can double-click the file.

### Using the Interface

#### Basic Settings Tab

1. **File Selection**:
   - Click "Browse..." next to Audio File and select your MP3/audio file
   - Click "Browse..." next to Lyrics File and select your lyrics text file
   - Optionally specify an output path (auto-generated if left empty)

2. **Whisper Model**:
   - Choose from tiny, base, small, medium, or large
   - Larger models are more accurate but slower

3. **Visual Settings**:
   - Text Color: white, yellow, cyan, green, magenta, red, blue

4. **Processing Options**:
   - ✓ LRC file is always generated
   - ☑ Skip video creation - Generate only synced lyrics file
   - ☑ Use CPU instead of GPU - Force CPU processing (slower)
   - ☑ Debug mode - Show verbose output

#### Visual Effects Tab

**Background Settings:**
- **Background Image**: Select an image file (PNG, JPG, etc.) to use as the video background
  - Image will be scaled and centered to fit 1280x720 resolution
  - Leave empty to use solid color
- **Background Color**: Choose a solid color (used if no image is selected)
  - Options: black, white, blue, red, green, gray, purple, navy

**Audio Equalizer:**
- **Show Audio Equalizer**: Enable/disable the frequency visualizer
- **Position**: Where to place the equalizer
  - bottom, top, or center
- **Height**: Vertical size of the equalizer (50-400 pixels)
- **Number of Bars**: How many frequency bars to display (10-40)
- **Equalizer Color**: Color of the frequency bars
  - Options: white, red, blue, green, yellow, cyan, magenta, orange, purple

#### Advanced Parameters Tab

Fine-tune the alignment algorithm:

- **Match Threshold** (40-80): Lower = more matches but less accurate
- **Search Window** (20-50s): How far to search for lyrics
- **Anchor Check Interval** (2-5): How often to verify alignment
- **Overlap Weight** (0.2-0.6): Weight given to exact word matches
- **Global Time Offset** (-3.0 to +3.0s): Shift all lyrics in time
- **Speed Multiplier** (0.9-1.1): Adjust overall pacing
- **Empty Line Gap** (0.0-2.0s): Spacing for blank lines
- **Section Header Gap** (0.0-3.0s): Spacing for section headers
- **Min Line Spacing** (0.5-5.0s): Minimum time between lines
- **Start/End Offsets** (0.0-10.0s): Padding at song boundaries

#### Metadata Tab

Optional metadata to embed in the LRC file:
- Title
- Artist
- Album

### Running the Conversion

1. Configure all settings as desired
2. Click the **"Process"** button
3. Monitor progress in the console output area
4. Wait for the "Processing complete!" message

### Resetting Parameters

Click **"Reset to Defaults"** to restore all parameters to their original values.

## Output Files

The script generates:
- **MP4 video file**: Audio with synchronized lyrics overlay
- **LRC file**: Synced lyrics file (can be used with media players)

## Tips for Best Results

1. **Start with defaults**: Try the default settings first
2. **If lyrics are too early/late**: Adjust "Global Time Offset"
3. **If lyrics drift over time**: Adjust "Speed Multiplier"
4. **If too many wrong matches**: Increase "Match Threshold"
5. **For songs with long instrumentals**: Increase "Search Window"

### Visual Effects Tips

1. **Background Images**:
   - Use high-resolution images (1920x1080 or higher) for best quality
   - Images will be scaled to 1280x720 and centered
   - Aspect ratio is preserved; black bars added if needed

2. **Equalizer Settings**:
   - Place at bottom for traditional look
   - Use smaller height (50-150px) for subtle effect
   - More bars (30-40) = smoother visualization
   - Fewer bars (10-15) = more dramatic movement
   - Match equalizer color to your lyrics color for cohesive look

## Troubleshooting

### GUI won't start
- Ensure Python 3.7+ is installed
- Check that tkinter is available: `python -m tkinter`

### "Cannot find script" error
- Make sure `lyrics_video_converter_tunable.py` is in the same folder as the GUI
- Or in the current working directory

### Processing fails
- Check the console output for error messages
- Ensure FFmpeg is installed and in your PATH
- Verify that audio and lyrics files are valid
- Try enabling debug mode for more information

### GPU not detected
- Install CUDA-compatible PyTorch: `pip install torch --index-url https://download.pytorch.org/whl/cu118`
- Check NVIDIA drivers are installed
- You can still use CPU mode (slower but works)

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- torch
- openai-whisper
- fuzzywuzzy
- python-Levenshtein
- FFmpeg (for video creation)

## Notes

- The GUI does not modify the original script's logic
- All parameters are passed as command-line arguments
- Processing runs in a separate thread to keep the GUI responsive
- Console output shows real-time progress from the script

## License

This GUI is provided as a companion tool for the lyrics video converter script.
