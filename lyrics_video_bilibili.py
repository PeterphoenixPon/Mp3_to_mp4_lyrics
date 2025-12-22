#!/usr/bin/env python3
"""
Advanced wrapper for creating Bilibili-style music videos
with album art, waveforms, and styled lyrics
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path
import json


def check_nvidia_gpu():
    """Check if NVIDIA GPU encoding (NVENC) is available"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode != 0:
            return False
        result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                              capture_output=True, text=True)
        if 'h264_nvenc' in result.stdout:
            return True
        return False
    except:
        return False


def create_bilibili_style_video(audio_path, lrc_path, output_path, bg_color='#1a3b5c',
                                text_color='white', album_art=None, title='', artist='',
                                waveform_config=None, force_cpu=False):
    """Create Bilibili-style video with album art, waveform, and styled lyrics"""
    
    sys.path.insert(0, os.path.dirname(__file__))
    from lyrics_video_converter_tunable import VideoCreator
    
    # Get audio duration
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
    except:
        duration = 300
    
    # Parse LRC file
    lyrics_data = VideoCreator._parse_lrc(lrc_path)
    if not lyrics_data:
        return False
    
    # Create styled subtitle file (Bilibili style)
    ass_path = str(Path(output_path).with_suffix('.ass'))
    create_bilibili_ass_subtitle(lyrics_data, ass_path, text_color, title, artist)
    
    # Escape paths
    ass_escaped = ass_path.replace('\\', '/').replace(':', '\\:')
    if album_art:
        album_art_escaped = album_art.replace('\\', '/').replace(':', '\\:')
    
    # GPU detection
    use_gpu = check_nvidia_gpu() and not force_cpu
    
    if use_gpu:
        print("🚀 Using NVIDIA GPU acceleration (NVENC)")
        video_codec = 'h264_nvenc'
        # Use faster preset for GPU
        codec_params = ['-preset', 'p2', '-tune', 'hq', '-rc', 'vbr', '-cq', '25', '-b:v', '5M']
    else:
        if force_cpu:
            print("⚠️  GPU encoding disabled by user, using CPU")
        else:
            print("⚠️  GPU not available, using CPU encoding")
        video_codec = 'libx264'
        # Use faster preset for CPU
        codec_params = ['-preset', 'veryfast', '-crf', '23']
    
    print("Creating Bilibili-style video...\n")
    
    # Build complex filter for Bilibili style
    if album_art and os.path.exists(album_art):
        # With album art - create layout
        if waveform_config and waveform_config.get('enabled'):
            # Full Bilibili style: background + album art + waveform + lyrics
            filter_complex = build_bilibili_filter_with_art_and_wave(
                bg_color, ass_escaped, album_art_escaped, waveform_config
            )
        else:
            # Background + album art + lyrics (no waveform)
            filter_complex = build_bilibili_filter_with_art(
                bg_color, ass_escaped, album_art_escaped
            )
        
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error', '-stats',
            '-f', 'lavfi', '-i', f'color=c={bg_color}:s=1920x1080:d={duration}',
            '-loop', '1', '-i', album_art,
            '-i', audio_path,
            '-filter_complex', filter_complex,
            '-map', '[v]', '-map', '2:a',
            '-c:v', video_codec, *codec_params,
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', '-pix_fmt', 'yuv420p',
            '-t', str(duration),
            output_path
        ]
    else:
        # Without album art - simpler style
        if waveform_config and waveform_config.get('enabled'):
            filter_complex = build_bilibili_filter_no_art_with_wave(
                bg_color, ass_escaped, waveform_config
            )
        else:
            filter_complex = f"[0:v]ass='{ass_escaped}'[v]"
        
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error', '-stats',
            '-f', 'lavfi', '-i', f'color=c={bg_color}:s=1920x1080:d={duration}',
            '-i', audio_path,
            '-filter_complex', filter_complex,
            '-map', '[v]', '-map', '1:a',
            '-c:v', video_codec, *codec_params,
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', '-pix_fmt', 'yuv420p',
            output_path
        ]
    
    print(f"Rendering Bilibili-style video...\n")
    result = subprocess.run(cmd)
    
    # Cleanup
    if os.path.exists(ass_path):
        os.remove(ass_path)
    
    if result.returncode == 0:
        print(f"\n✓ Video created: {output_path}")
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
        return True
    
    return False


def build_bilibili_filter_with_art_and_wave(bg_color, ass_path, album_art, wave_config):
    """Build filter for full Bilibili style with album art and waveform - OPTIMIZED"""
    wave_color = get_wave_color(wave_config.get('color', 'white'))
    wave_height = wave_config.get('size', 80)
    
    # OPTIMIZATION: Use smaller blur resolution (1920x1080 instead of 9600x5400)
    # This is 25x fewer pixels to process!
    filter_parts = [
        # Create blurred background - process at output resolution for speed
        f"[1:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=40,format=yuva420p,colorchannelmixer=aa=0.3[bg_blur]",
        
        # Overlay blurred background
        f"[0:v][bg_blur]overlay=0:0[bg]",
        
        # Prepare album art - simpler, no separate shadow pass
        f"[1:v]scale=600:600:force_original_aspect_ratio=decrease,pad=600:600:(ow-iw)/2:(oh-ih)/2:color=#00000000[art]",
        
        # Create waveform visualization - use simpler mode
        f"[2:a]showwaves=s=800x{wave_height}:mode=line:colors={wave_color}:scale=lin:rate=25[wave]",
        
        # Composite everything
        f"[bg][art]overlay=100:240[bg_with_art]",
        f"[bg_with_art][wave]overlay=960:880[base]",
        
        # Add subtitles
        f"[base]ass='{ass_path}'[v]"
    ]
    
    return ';'.join(filter_parts)


def build_bilibili_filter_with_art(bg_color, ass_path, album_art):
    """Build filter for Bilibili style with album art (no waveform) - OPTIMIZED"""
    filter_parts = [
        # Create blurred background at output resolution
        f"[1:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=40,format=yuva420p,colorchannelmixer=aa=0.3[bg_blur]",
        
        # Overlay blurred background
        f"[0:v][bg_blur]overlay=0:0[bg]",
        
        # Prepare album art
        f"[1:v]scale=600:600:force_original_aspect_ratio=decrease,pad=600:600:(ow-iw)/2:(oh-ih)/2:color=#00000000[art]",
        
        # Composite
        f"[bg][art]overlay=100:240[base]",
        f"[base]ass='{ass_path}'[v]"
    ]
    
    return ';'.join(filter_parts)


def build_bilibili_filter_no_art_with_wave(bg_color, ass_path, wave_config):
    """Build filter for Bilibili style without album art but with waveform"""
    wave_color = get_wave_color(wave_config.get('color', 'white'))
    wave_height = wave_config.get('size', 80)
    
    filter_parts = [
        f"[1:a]showwaves=s=1200x{wave_height}:mode=line:colors={wave_color}:scale=sqrt:rate=25[wave]",
        f"[0:v][wave]overlay=(W-w)/2:(H-h)-100[base]",
        f"[base]ass='{ass_path}'[v]"
    ]
    
    return ';'.join(filter_parts)


def create_bilibili_ass_subtitle(lyrics_data, ass_path, text_color, title='', artist=''):
    """Create Bilibili-style ASS subtitle with proper positioning and styling"""
    
    color_map = {
        'white': '&H00FFFFFF', 'yellow': '&H0000FFFF',
        'cyan': '&H00FFFF00', 'green': '&H0000FF00',
        'magenta': '&H00FF00FF', 'red': '&H000000FF',
        'blue': '&H00FF0000'
    }
    ass_color = color_map.get(text_color.lower(), '&H00FFFFFF')
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write("[Script Info]\n")
        f.write("Title: Bilibili Style Lyrics\n")
        f.write("ScriptType: v4.00+\n")
        f.write("WrapStyle: 0\n")
        f.write("PlayResX: 1920\n")
        f.write("PlayResY: 1080\n\n")
        
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        
        # Main lyrics style - positioned on right side
        f.write(f"Style: Main,Arial,60,{ass_color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,7,850,100,400,1\n")
        
        # Title style - top right
        f.write(f"Style: Title,Arial,48,{ass_color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,9,850,100,120,1\n")
        
        # Info style - smaller text for metadata
        f.write(f"Style: Info,Arial,32,{ass_color},&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,9,850,100,200,1\n\n")
        
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        
        # Add title and artist (persistent throughout video)
        if title:
            f.write(f"Dialogue: 1,0:00:00.00,{format_ass_time(lyrics_data[-1][0] + 5)},Title,,0,0,0,,{escape_ass(title)}\n")
        
        if artist:
            f.write(f"Dialogue: 1,0:00:00.00,{format_ass_time(lyrics_data[-1][0] + 5)},Info,,0,0,0,,{{\\pos(1410,220)}}{escape_ass(f'演唱: {artist}')}\n")
        
        # Add lyrics with fade effects
        for i, (timestamp, lyric) in enumerate(lyrics_data):
            start_time = format_ass_time(timestamp)
            
            if i + 1 < len(lyrics_data):
                end_time = format_ass_time(lyrics_data[i + 1][0])
            else:
                end_time = format_ass_time(timestamp + 5)
            
            # Add fade in/out effect
            lyric_escaped = escape_ass(lyric)
            f.write(f"Dialogue: 0,{start_time},{end_time},Main,,0,0,0,,{{\\fad(200,200)}}{lyric_escaped}\n")


def escape_ass(text):
    """Escape special characters for ASS format"""
    return text.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')


def format_ass_time(seconds):
    """Format timestamp for ASS subtitle"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def get_wave_color(color):
    """Get FFmpeg color for waveform"""
    color_map = {
        'white': 'white',
        'red': 'red',
        'blue': 'blue',
        'green': 'green',
        'yellow': 'yellow',
        'cyan': 'cyan',
        'magenta': 'magenta',
        'orange': 'orange',
        'purple': 'purple'
    }
    return color_map.get(color, 'white')


def main():
    parser = argparse.ArgumentParser(description="Bilibili-style video creator")
    parser.add_argument('audio', help='Input audio file')
    parser.add_argument('lrc', help='Input LRC file')
    parser.add_argument('output', help='Output video file')
    parser.add_argument('--bg-color', default='#1a3b5c', help='Background color (hex)')
    parser.add_argument('--text-color', default='white')
    parser.add_argument('--album-art', help='Album artwork path')
    parser.add_argument('--title', default='', help='Song title')
    parser.add_argument('--artist', default='', help='Artist name')
    parser.add_argument('--waveform', help='Waveform config JSON')
    parser.add_argument('--no-gpu-encoding', action='store_true')
    
    args = parser.parse_args()
    
    # Parse waveform config
    wave_config = None
    if args.waveform:
        try:
            wave_config = json.loads(args.waveform)
        except:
            print("Warning: Failed to parse waveform config")
    
    success = create_bilibili_style_video(
        args.audio,
        args.lrc,
        args.output,
        args.bg_color,
        args.text_color,
        args.album_art,
        args.title,
        args.artist,
        wave_config,
        args.no_gpu_encoding
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())