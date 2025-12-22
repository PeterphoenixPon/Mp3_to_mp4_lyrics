# Quick Start Guide

## 5-Minute Setup

### Step 1: Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

**Mac:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org and add to PATH

### Step 2: Run the Program

```bash
python lyrics_video_converter.py your_song.mp3 your_lyrics.txt
```

That's it! The program will:
1. Auto-install Python packages (first time only)
2. Download the Whisper model (first time only, ~100MB)
3. Transcribe your audio
4. Sync your lyrics
5. Create a video with lyrics

## Common Commands

### Just want timestamped lyrics?
```bash
python lyrics_video_converter.py song.mp3 lyrics.txt --lrc-only
```

### Want custom colors?
```bash
python lyrics_video_converter.py song.mp3 lyrics.txt \
  --bg-color blue --text-color yellow
```

### Need better accuracy?
```bash
python lyrics_video_converter.py song.mp3 lyrics.txt --model medium
```

## Expected Time

- **tiny model**: 1-2 minutes per song
- **base model**: 3-5 minutes per song (recommended)
- **medium model**: 10-15 minutes per song
- **large model**: 20-30 minutes per song

First run will be longer due to model download.

## Checklist

- [ ] FFmpeg installed (`ffmpeg -version` should work)
- [ ] Python 3.8+ installed (`python --version`)
- [ ] Have your MP3 file
- [ ] Have your lyrics in a .txt file
- [ ] Run the command
- [ ] Wait for it to finish
- [ ] Enjoy your video!

## What You Get

After running, you'll have two files:
1. **`song_synced.lrc`** - Timestamped lyrics (open in text editor or music player)
2. **`song_with_lyrics.mp4`** - Video with animated lyrics

## Troubleshooting

**"ffmpeg: command not found"**
→ Install FFmpeg (see Step 1)

**Slow processing?**
→ Use `--model tiny` for faster results

**Poor sync quality?**
→ Use `--model medium` for better accuracy

**Want to adjust timestamps?**
→ Edit the `.lrc` file in a text editor, then re-run without `--lrc-only`

## Full Documentation

See README.md for complete documentation and advanced features.
