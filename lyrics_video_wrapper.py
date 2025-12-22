#!/usr/bin/env python3
"""
Wrapper script that adds background image and equalizer support
to the lyrics_video_converter_tunable.py script
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
        # Check if nvidia-smi exists
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode != 0:
            return False
        
        # Check if FFmpeg has h264_nvenc support
        result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                              capture_output=True, text=True)
        if 'h264_nvenc' in result.stdout:
            return True
        return False
    except:
        return False


def create_video_with_effects(audio_path, lrc_path, output_path, bg_color='black', 
                              text_color='white', bg_image=None, equalizer_config=None, force_cpu=False):
    """Create video with optional background image and equalizer"""
    
    # Import the video creator from the main script
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
    
    # Create ASS subtitle file
    ass_path = str(Path(output_path).with_suffix('.ass'))
    VideoCreator._create_ass_subtitle(lyrics_data, ass_path, text_color)
    
    # Escape ASS path for FFmpeg
    ass_escaped = ass_path.replace('\\', '/').replace(':', '\\:')
    
    # Check for GPU support
    use_gpu = check_nvidia_gpu() and not force_cpu
    
    if use_gpu:
        print("🚀 Using NVIDIA GPU acceleration (NVENC)")
        video_codec = 'h264_nvenc'
        codec_params = ['-preset', 'p4', '-tune', 'hq', '-rc', 'vbr', '-cq', '23']
    else:
        if force_cpu:
            print("⚠️  GPU encoding disabled by user, using CPU")
        else:
            print("⚠️  GPU not available, using CPU encoding")
        video_codec = 'libx264'
        codec_params = ['-preset', 'fast', '-crf', '23']
    
    # Build FFmpeg command
    if bg_image and os.path.exists(bg_image):
        # Use background image
        print("Using background image...")
        
        if equalizer_config and equalizer_config.get('enabled'):
            # With equalizer
            video_filter = f"[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1:color={bg_color},setsar=1,ass='{ass_escaped}'[vid];[1:a]showfreqs=mode=bar:ascale=sqrt:fscale=log:win_size=2048:colors={get_eq_color(equalizer_config.get('color', 'white'))}:s=1280x{equalizer_config.get('size', 200)}[eq];[vid][eq]overlay=0:{get_eq_position(equalizer_config.get('position', 'bottom'), equalizer_config.get('size', 200))}:format=auto[v]"
            
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'error', '-stats',
                '-loop', '1', '-i', bg_image,
                '-i', audio_path,
                '-filter_complex', video_filter,
                '-map', '[v]', '-map', '1:a',
                '-c:v', video_codec, *codec_params,
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
        else:
            # Without equalizer - simpler filter
            video_filter = f"[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1:color={bg_color},setsar=1,ass='{ass_escaped}'[v]"
            
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'error', '-stats',
                '-loop', '1', '-i', bg_image,
                '-i', audio_path,
                '-filter_complex', video_filter,
                '-map', '[v]', '-map', '1:a',
                '-c:v', video_codec, *codec_params,
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
    else:
        # Use solid color background
        print("Using solid color background...")
        
        if equalizer_config and equalizer_config.get('enabled'):
            video_filter = f"[0:v]ass='{ass_escaped}'[vid];[1:a]showfreqs=mode=bar:ascale=sqrt:fscale=log:win_size=2048:colors={get_eq_color(equalizer_config.get('color', 'white'))}:s=1280x{equalizer_config.get('size', 200)}[eq];[vid][eq]overlay=0:{get_eq_position(equalizer_config.get('position', 'bottom'), equalizer_config.get('size', 200))}:format=auto[v]"
            
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'error', '-stats',
                '-f', 'lavfi', '-i', f'color=c={bg_color}:s=1280x720:d={duration}',
                '-i', audio_path,
                '-filter_complex', video_filter,
                '-map', '[v]', '-map', '1:a',
                '-c:v', video_codec, *codec_params,
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-pix_fmt', 'yuv420p',
                output_path
            ]
        else:
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'error', '-stats',
                '-f', 'lavfi', '-i', f'color=c={bg_color}:s=1280x720:d={duration}',
                '-i', audio_path,
                '-vf', f"ass='{ass_escaped}'",
                '-c:v', video_codec, *codec_params,
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-pix_fmt', 'yuv420p',
                output_path
            ]
    
    print(f"Rendering video with effects...\n")
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


def get_eq_color(color):
    """Get FFmpeg color code for equalizer"""
    color_map = {
        'white': '0xFFFFFF',
        'red': '0xFF0000',
        'blue': '0x0000FF',
        'green': '0x00FF00',
        'yellow': '0xFFFF00',
        'cyan': '0x00FFFF',
        'magenta': '0xFF00FF',
        'orange': '0xFFA500',
        'purple': '0x800080'
    }
    return color_map.get(color, '0xFFFFFF')


def get_eq_position(position, height):
    """Calculate equalizer Y position"""
    if position == 'bottom':
        return f'(H-{height})'
    elif position == 'top':
        return '0'
    else:  # center
        return f'(H-{height})/2'


def main():
    parser = argparse.ArgumentParser(description="Video wrapper with effects support")
    parser.add_argument('audio', help='Input audio file')
    parser.add_argument('lrc', help='Input LRC file')
    parser.add_argument('output', help='Output video file')
    parser.add_argument('--bg-color', default='black')
    parser.add_argument('--text-color', default='white')
    parser.add_argument('--bg-image', help='Background image path')
    parser.add_argument('--equalizer', help='Equalizer config JSON')
    parser.add_argument('--no-gpu-encoding', action='store_true', help='Disable GPU encoding')
    
    args = parser.parse_args()
    
    # Parse equalizer config
    eq_config = None
    if args.equalizer:
        try:
            eq_config = json.loads(args.equalizer)
        except:
            print("Warning: Failed to parse equalizer config")
    
    success = create_video_with_effects(
        args.audio,
        args.lrc,
        args.output,
        args.bg_color,
        args.text_color,
        args.bg_image,
        eq_config,
        args.no_gpu_encoding
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())