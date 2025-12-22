#!/usr/bin/env python3
"""
MP3 to MP4 Converter - GPU OPTIMIZED with ADJUSTABLE PARAMETERS

Easy-to-tune parameters at the top of the file!
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
import subprocess
import re
import warnings

# ============================================================================
# ADJUSTABLE PARAMETERS - TUNE THESE FOR BETTER ALIGNMENT
# ============================================================================

class AlignmentConfig:
    """
    Configuration for alignment - ADJUST THESE VALUES
    """
    
    # MATCHING QUALITY
    # Lower = more matches (better coverage, less accurate)
    # Higher = fewer matches (less coverage, more accurate)
    MATCH_THRESHOLD = 55  # Range: 40-80, Default: 60
    
    # SEARCH WINDOW (seconds)
    # How far from expected position to search for lyrics
    # Larger = can find lyrics further away (good for songs with instrumentals)
    SEARCH_WINDOW = 40  # Range: 20-50, Default: 30
    
    # ANCHOR FREQUENCY
    # Check every N lines for high-confidence matches
    # Lower = more anchors (more accurate, slower)
    # Higher = fewer anchors (faster, may drift)
    ANCHOR_CHECK_INTERVAL = 2  # Range: 2-5, Default: 3
    
    # WORD OVERLAP WEIGHT
    # How much to weight exact word matches vs overall similarity
    # Higher overlap weight = prioritize exact word matches
    OVERLAP_WEIGHT = 0.4  # Range: 0.2-0.6, Default: 0.4
    
    # TIMING ADJUSTMENTS
    # Global time offset (seconds) - positive = lyrics appear later
    GLOBAL_TIME_OFFSET = 0.0  # Range: -3.0 to +3.0, Default: 0.0
    
    # Speed adjustment multiplier for lyrics
    # >1.0 = lyrics spread out more (slower pacing)
    # <1.0 = lyrics compressed (faster pacing)
    SPEED_MULTIPLIER = 1.0  # Range: 0.9-1.1, Default: 1.0
    
    # SPACING FOR NON-LYRIC LINES
    EMPTY_LINE_GAP = 0.1  # Seconds after previous line, Default: 0.5
    SECTION_HEADER_GAP = 0.1  # Seconds after previous line, Default: 1.0
    
    # MINIMUM TIME BETWEEN LYRICS (prevents lines being too close)
    MIN_LINE_SPACING = 3  # Seconds, Default: 1.5
    
    # BOUNDARY OFFSETS
    # How far from start/end of song to place first/last lyrics
    START_OFFSET = 3.0  # Seconds from start, Default: 3.0
    END_OFFSET = 3.0    # Seconds from end, Default: 5.0

# ============================================================================

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

try:
    import torch
    import whisper
    from fuzzywuzzy import fuzz
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "torch", "openai-whisper", "fuzzywuzzy", 
                          "python-Levenshtein", "-q"])
    import torch
    import whisper
    from fuzzywuzzy import fuzz


def check_gpu():
    """Check GPU availability"""
    print("\n" + "="*60)
    print("GPU Detection")
    print("="*60)
    
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"✓ CUDA Available: YES")
        print(f"✓ GPU: {gpu_name}")
        print(f"✓ Memory: {gpu_memory:.1f} GB")
        print(f"✓ CUDA Version: {torch.version.cuda}")
        print("\n🚀 GPU acceleration ENABLED\n")
        return True
    else:
        print("⚠️  CUDA Available: NO")
        print("ℹ️  Running on CPU\n")
        return False


class LyricSynchronizer:
    """Synchronizes lyrics with audio using Whisper"""
    
    def __init__(self, model_size="medium", debug=False, use_gpu=True, config=None):
        self.debug = debug
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.config = config or AlignmentConfig()
        
        print(f"{'='*60}")
        print(f"Loading Whisper {model_size} model...")
        print(f"{'='*60}")
        
        device = "cuda" if self.use_gpu else "cpu"
        print(f"Device: {device.upper()}")
        
        # Show config
        print(f"\nAlignment Configuration:")
        print(f"  Match threshold: {self.config.MATCH_THRESHOLD}")
        print(f"  Search window: {self.config.SEARCH_WINDOW}s")
        print(f"  Anchor interval: every {self.config.ANCHOR_CHECK_INTERVAL} lines")
        print(f"  Global offset: {self.config.GLOBAL_TIME_OFFSET:+.1f}s")
        print(f"  Speed multiplier: {self.config.SPEED_MULTIPLIER}x")
        
        self.model = whisper.load_model(model_size, device=device)
        print("\n✓ Model loaded\n")
        
    def transcribe_audio(self, audio_path: str) -> Dict:
        """Transcribe with word-level timestamps"""
        print(f"{'='*60}")
        print(f"Transcribing: {Path(audio_path).name}")
        print(f"{'='*60}\n")
        
        if self.use_gpu:
            print("🚀 Using GPU acceleration...\n")
        
        result = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            verbose=False,
            language='en',
            fp16=self.use_gpu
        )
        
        segments = result.get('segments', [])
        
        if segments:
            duration = segments[-1]['end']
            total_words = sum(len(seg.get('words', [])) for seg in segments)
            
            print(f"✓ Transcription complete!")
            print(f"  Duration: {duration:.1f}s ({duration/60:.1f} min)")
            print(f"  Segments: {len(segments)}")
            print(f"  Words: {total_words}\n")
            
            if self.debug:
                print("=== TRANSCRIPTION PREVIEW ===")
                print(result['text'][:300] + "...\n")
        
        return result
    
    def align_lyrics(self, lyrics_lines: List[str], transcription: Dict) -> List[Tuple[float, str]]:
        """Align lyrics with transcription"""
        print(f"{'='*60}")
        print("Aligning lyrics with transcription")
        print(f"{'='*60}\n")
        
        segments = transcription.get('segments', [])
        
        if not segments:
            print("⚠️  No transcription available!")
            return [(0, line.strip()) for line in lyrics_lines if line.strip()]
        
        # Extract content lines (non-headers, non-empty)
        content_lines = []
        for line in lyrics_lines:
            stripped = line.strip()
            if stripped and not self._is_section_header(stripped):
                content_lines.append(stripped)
        
        song_duration = segments[-1]['end']
        
        print(f"Content lines: {len(content_lines)}")
        print(f"Song duration: {song_duration:.1f}s\n")
        
        # Find anchor points - USES CONFIG.ANCHOR_CHECK_INTERVAL
        print("Finding anchor points...")
        anchors = self._find_anchor_points(content_lines, segments)
        print(f"✓ Found {len(anchors)} anchors\n")
        
        if self.debug and anchors:
            print("Anchor points:")
            for idx, time in anchors[:5]:
                print(f"  Line {idx:3d} @ {time:6.1f}s: {content_lines[idx][:50]}...")
            print()
        
        # Interpolate timestamps - USES CONFIG.SPEED_MULTIPLIER
        print("Interpolating timestamps...")
        timestamped_content = self._interpolate_timestamps(
            content_lines, 
            anchors, 
            song_duration
        )
        
        # Apply global offset - USES CONFIG.GLOBAL_TIME_OFFSET
        if self.config.GLOBAL_TIME_OFFSET != 0:
            print(f"Applying global offset: {self.config.GLOBAL_TIME_OFFSET:+.1f}s")
            timestamped_content = [
                (t + self.config.GLOBAL_TIME_OFFSET, line) 
                for t, line in timestamped_content
            ]
        
        # Enforce minimum spacing - USES CONFIG.MIN_LINE_SPACING
        timestamped_content = self._enforce_minimum_spacing(timestamped_content)
        
        # Rebuild with headers/empty lines - USES CONFIG SPACING VALUES
        timestamped_lyrics = self._rebuild_with_headers(
            lyrics_lines, 
            content_lines, 
            timestamped_content
        )
        
        # Validation
        self._validate_alignment(timestamped_lyrics, song_duration)
        
        return timestamped_lyrics
    
    def _find_anchor_points(self, content_lines: List[str], 
                           segments: List[Dict]) -> List[Tuple[int, float]]:
        """
        Find high-confidence matches throughout the song
        USES: CONFIG.ANCHOR_CHECK_INTERVAL, CONFIG.MATCH_THRESHOLD, CONFIG.SEARCH_WINDOW
        """
        anchors = []
        
        # Check every Nth line - CONFIGURABLE
        for line_idx in range(0, len(content_lines), self.config.ANCHOR_CHECK_INTERVAL):
            lyric = content_lines[line_idx]
            clean_lyric = self._clean_for_matching(lyric)
            
            if not clean_lyric or len(clean_lyric) < 10:
                continue
            
            # Expected position
            expected_time = (line_idx / len(content_lines)) * segments[-1]['end']
            
            # Search around expected time - CONFIGURABLE WINDOW
            best_match = self._find_best_match_in_window(
                clean_lyric, 
                segments, 
                expected_time,
                self.config.SEARCH_WINDOW
            )
            
            # Accept if above threshold - CONFIGURABLE THRESHOLD
            if best_match and best_match['score'] > self.config.MATCH_THRESHOLD:
                anchors.append((line_idx, best_match['time']))
                
                if self.debug:
                    print(f"  Anchor: Line {line_idx} @ {best_match['time']:.1f}s "
                          f"(score: {best_match['score']:.0f})")
        
        return anchors
    
    def _find_best_match_in_window(self, clean_lyric: str, segments: List[Dict],
                                   expected_time: float, window: float) -> Dict:
        """
        Find best match within time window
        USES: CONFIG.OVERLAP_WEIGHT
        """
        best_match = None
        best_score = 0
        
        start_time = max(0, expected_time - window)
        end_time = expected_time + window
        
        for seg in segments:
            if seg['start'] < start_time or seg['start'] > end_time:
                continue
            
            clean_seg = self._clean_for_matching(seg['text'])
            
            if not clean_seg:
                continue
            
            # Multiple matching strategies
            scores = [
                fuzz.partial_ratio(clean_lyric, clean_seg),
                fuzz.token_sort_ratio(clean_lyric, clean_seg),
                fuzz.token_set_ratio(clean_lyric, clean_seg)
            ]
            
            score = max(scores)
            
            # Word overlap bonus - CONFIGURABLE WEIGHT
            lyric_words = set(clean_lyric.split())
            seg_words = set(clean_seg.split())
            if lyric_words and seg_words:
                overlap = len(lyric_words & seg_words) / len(lyric_words)
                base_weight = 1.0 - self.config.OVERLAP_WEIGHT
                score = score * (base_weight + self.config.OVERLAP_WEIGHT * overlap)
            
            if score > best_score:
                best_score = score
                best_match = {
                    'time': seg['start'],
                    'score': score,
                    'text': seg['text']
                }
        
        return best_match
    
    def _interpolate_timestamps(self, content_lines: List[str],
                               anchors: List[Tuple[int, float]],
                               total_duration: float) -> List[Tuple[float, str]]:
        """
        Interpolate timestamps between anchors
        USES: CONFIG.START_OFFSET, CONFIG.END_OFFSET, CONFIG.SPEED_MULTIPLIER
        """
        
        if not anchors:
            # Even distribution
            interval = (total_duration - self.config.START_OFFSET - self.config.END_OFFSET) / (len(content_lines) + 1)
            return [(self.config.START_OFFSET + i * interval, line) 
                    for i, line in enumerate(content_lines, 1)]
        
        # Add boundary anchors - CONFIGURABLE OFFSETS
        if anchors[0][0] > 0:
            anchors.insert(0, (0, self.config.START_OFFSET))
        
        if anchors[-1][0] < len(content_lines) - 1:
            anchors.append((len(content_lines) - 1, total_duration - self.config.END_OFFSET))
        
        # Interpolate
        timestamped = []
        
        for i in range(len(anchors) - 1):
            start_idx, start_time = anchors[i]
            end_idx, end_time = anchors[i + 1]
            
            num_lines = end_idx - start_idx
            if num_lines <= 0:
                continue
            
            # Apply speed multiplier - CONFIGURABLE
            time_per_line = ((end_time - start_time) / num_lines) * self.config.SPEED_MULTIPLIER
            
            for j in range(num_lines):
                line_idx = start_idx + j
                if line_idx < len(content_lines):
                    timestamp = start_time + (j * time_per_line)
                    timestamped.append((timestamp, content_lines[line_idx]))
        
        # Add remaining
        if len(timestamped) < len(content_lines):
            last_time = anchors[-1][1]
            for i in range(len(timestamped), len(content_lines)):
                timestamped.append((last_time, content_lines[i]))
        
        return timestamped
    
    def _enforce_minimum_spacing(self, timestamped: List[Tuple[float, str]]) -> List[Tuple[float, str]]:
        """
        Ensure minimum time between lines
        USES: CONFIG.MIN_LINE_SPACING
        """
        if len(timestamped) < 2:
            return timestamped
        
        adjusted = [timestamped[0]]
        
        for i in range(1, len(timestamped)):
            prev_time = adjusted[-1][0]
            curr_time, line = timestamped[i]
            
            # Ensure minimum spacing
            if curr_time - prev_time < self.config.MIN_LINE_SPACING:
                curr_time = prev_time + self.config.MIN_LINE_SPACING
            
            adjusted.append((curr_time, line))
        
        return adjusted
    
    def _rebuild_with_headers(self, original_lines: List[str],
                             content_lines: List[str],
                             timestamped_content: List[Tuple[float, str]]) -> List[Tuple[float, str]]:
        """
        Rebuild full lyrics with headers and empty lines
        USES: CONFIG.EMPTY_LINE_GAP, CONFIG.SECTION_HEADER_GAP
        
        This is the function you asked about!
        """
        result = []
        content_idx = 0
        
        for line in original_lines:
            stripped = line.strip()
            
            # CASE 1: Empty line
            if not stripped:
                if result:
                    # Add empty line with gap - CONFIGURABLE
                    result.append((result[-1][0] + self.config.EMPTY_LINE_GAP, ""))
                continue
            
            # CASE 2: Section header (Verse 1:, Chorus:, etc.)
            if self._is_section_header(stripped):
                if result:
                    # Add header with gap - CONFIGURABLE
                    result.append((result[-1][0] + self.config.SECTION_HEADER_GAP, stripped))
                else:
                    result.append((0.0, stripped))
                continue
            
            # CASE 3: Actual lyric content
            if content_idx < len(timestamped_content):
                timestamp, _ = timestamped_content[content_idx]
                result.append((timestamp, stripped))
                content_idx += 1
        
        return sorted(result, key=lambda x: x[0])
    
    def _validate_alignment(self, timestamped_lyrics: List[Tuple[float, str]],
                           song_duration: float):
        """Validate final alignment"""
        if not timestamped_lyrics:
            return
        
        first_time = min((t for t, _ in timestamped_lyrics if t > 0), default=0)
        last_time = max((t for t, _ in timestamped_lyrics), default=0)
        coverage = (last_time / song_duration) * 100 if song_duration > 0 else 0
        
        print(f"{'='*60}")
        print("Alignment Summary")
        print(f"{'='*60}")
        print(f"✓ Total lines: {len(timestamped_lyrics)}")
        print(f"  First line: {first_time:.1f}s")
        print(f"  Last line: {last_time:.1f}s")
        print(f"  Song duration: {song_duration:.1f}s")
        print(f"  Coverage: {coverage:.1f}%")
        
        if coverage < 70:
            print(f"\n⚠️  Low coverage - try lowering MATCH_THRESHOLD")
        elif coverage > 110:
            print(f"\n⚠️  High coverage - check for timing issues")
        else:
            print(f"\n✓ Coverage is good!")
        
        print()
    
    def _is_section_header(self, text: str) -> bool:
        """Check if line is a section header"""
        patterns = [
            r'^(Verse|Chorus|Bridge|Intro|Outro|Pre-?Chorus|Hook|Refrain)',
            r'^\[.*\]$',
            r'^(V\d|C\d)',
        ]
        
        for pattern in patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return len(text) < 20 and text.endswith(':')
    
    def _clean_for_matching(self, text: str) -> str:
        """Clean text for matching"""
        text = text.lower()
        fillers = ['oh', 'ah', 'yeah', 'hey', 'whoa', 'ooh', 'mmm', 'la', 'na']
        words = [w for w in text.split() if w not in fillers]
        text = ' '.join(words)
        text = re.sub(r"[^\w\s']", ' ', text)
        return ' '.join(text.split())


class LRCWriter:
    """Write timestamped lyrics to LRC format"""
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"[{minutes:02d}:{secs:05.2f}]"
    
    @staticmethod
    def write_lrc(timestamped_lyrics: List[Tuple[float, str]], 
                  output_path: str, metadata: Dict = None):
        with open(output_path, 'w', encoding='utf-8') as f:
            if metadata:
                if 'title' in metadata:
                    f.write(f"[ti:{metadata['title']}]\n")
                if 'artist' in metadata:
                    f.write(f"[ar:{metadata['artist']}]\n")
                if 'album' in metadata:
                    f.write(f"[al:{metadata['album']}]\n")
                f.write("\n")
            
            for timestamp, lyric in sorted(timestamped_lyrics):
                time_str = LRCWriter.format_timestamp(timestamp)
                f.write(f"{time_str}{lyric}\n")
        
        print(f"✓ LRC file saved: {output_path}")


class VideoCreator:
    """Create MP4 video with animated lyrics"""
    
    @staticmethod
    def create_video(audio_path: str, lrc_path: str, output_path: str,
                     background_color: str = "black", text_color: str = "white"):
        print(f"\n{'='*60}")
        print(f"Creating video")
        print(f"{'='*60}\n")
        
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except:
            print("❌ FFmpeg not found!")
            return False
        
        lyrics_data = VideoCreator._parse_lrc(lrc_path)
        if not lyrics_data:
            return False
        
        ass_path = str(Path(output_path).with_suffix('.ass'))
        VideoCreator._create_ass_subtitle(lyrics_data, ass_path, text_color)
        
        try:
            duration = VideoCreator._get_audio_duration(audio_path)
        except:
            duration = 300
        
        print(f"Rendering video...\n")
        # Escape the ASS path for FFmpeg filter syntax
        # FFmpeg filters need: backslashes to forward slashes, escape colons and backslashes
        ass_escaped = ass_path.replace('\\', '/').replace(':', '\\:')
        
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error', '-stats',
            '-f', 'lavfi', '-i', f'color=c={background_color}:s=1280x720:d={duration}',
            '-i', audio_path,
            '-vf', f"ass='{ass_escaped}'",
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', '-pix_fmt', 'yuv420p',
            output_path
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print(f"\n✓ Video created: {output_path}")
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"  Size: {size_mb:.1f} MB")
            if os.path.exists(ass_path):
                os.remove(ass_path)
            return True
        
        return False
    
    @staticmethod
    def _parse_lrc(lrc_path: str) -> List[Tuple[float, str]]:
        lyrics_data = []
        try:
            with open(lrc_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('[ti:') or line.startswith('[ar:') or line.startswith('[al:'):
                        continue
                    
                    if line.startswith('['):
                        try:
                            end_bracket = line.index(']')
                            time_str = line[1:end_bracket]
                            lyric = line[end_bracket+1:]
                            
                            parts = time_str.split(':')
                            minutes = int(parts[0])
                            seconds = float(parts[1])
                            total_seconds = minutes * 60 + seconds
                            
                            lyrics_data.append((total_seconds, lyric))
                        except:
                            continue
        except Exception as e:
            print(f"Error reading LRC: {e}")
        
        return lyrics_data
    
    @staticmethod
    def _create_ass_subtitle(lyrics_data: List[Tuple[float, str]], 
                            ass_path: str, text_color: str):
        color_map = {
            'white': '&H00FFFFFF', 'yellow': '&H0000FFFF',
            'cyan': '&H00FFFF00', 'green': '&H0000FF00',
            'magenta': '&H00FF00FF', 'red': '&H000000FF',
            'blue': '&H00FF0000'
        }
        ass_color = color_map.get(text_color.lower(), '&H00FFFFFF')
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write("[Script Info]\nTitle: Lyrics\nScriptType: v4.00+\n")
            f.write("WrapStyle: 0\nPlayResX: 1280\nPlayResY: 720\n\n")
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write(f"Style: Default,Arial,52,{ass_color},&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n\n")
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for i, (timestamp, lyric) in enumerate(lyrics_data):
                start_time = VideoCreator._format_ass_time(timestamp)
                if i + 1 < len(lyrics_data):
                    end_time = VideoCreator._format_ass_time(lyrics_data[i + 1][0])
                else:
                    end_time = VideoCreator._format_ass_time(timestamp + 4)
                
                lyric = lyric.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
                f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{lyric}\n")
    
    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    @staticmethod
    def _get_audio_duration(audio_path: str) -> float:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(
        description="MP3 to MP4 with Lyrics - GPU OPTIMIZED with TUNABLE PARAMETERS"
    )
    parser.add_argument('audio', help='Input audio file')
    parser.add_argument('lyrics', help='Input lyrics file')
    parser.add_argument('-o', '--output', help='Output MP4 file')
    parser.add_argument('-m', '--model', default='base',
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper model (default: base)')
    parser.add_argument('--lrc-only', action='store_true')
    parser.add_argument('--cpu', action='store_true')
    parser.add_argument('--bg-color', default='black')
    parser.add_argument('--text-color', default='white')
    parser.add_argument('--title', help='Song title')
    parser.add_argument('--artist', help='Artist name')
    parser.add_argument('--album', help='Album name')
    parser.add_argument('--debug', action='store_true')
    
    # Parameter overrides
    parser.add_argument('--threshold', type=int, help='Match threshold (40-80)')
    parser.add_argument('--offset', type=float, help='Global time offset in seconds')
    parser.add_argument('--speed', type=float, help='Speed multiplier (0.9-1.1)')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("MP3 to MP4 Converter - TUNABLE VERSION")
    print("="*60)
    
    # Create config with overrides
    config = AlignmentConfig()
    if args.threshold:
        config.MATCH_THRESHOLD = args.threshold
    if args.offset:
        config.GLOBAL_TIME_OFFSET = args.offset
    if args.speed:
        config.SPEED_MULTIPLIER = args.speed
    
    has_gpu = check_gpu()
    use_gpu = has_gpu and not args.cpu
    
    if not os.path.exists(args.audio) or not os.path.exists(args.lyrics):
        print("❌ File not found!")
        return 1
    
    audio_stem = Path(args.audio).stem
    output_video = args.output or f"{audio_stem}_with_lyrics.mp4"
    output_lrc = f"{audio_stem}_synced.lrc"
    
    with open(args.lyrics, 'r', encoding='utf-8') as f:
        lyrics_lines = f.readlines()
    
    print(f"\n📄 Lyrics lines: {len([l for l in lyrics_lines if l.strip()])}")
    
    import time
    start = time.time()
    
    synchronizer = LyricSynchronizer(
        model_size=args.model, 
        debug=args.debug, 
        use_gpu=use_gpu,
        config=config
    )
    transcription = synchronizer.transcribe_audio(args.audio)
    timestamped_lyrics = synchronizer.align_lyrics(lyrics_lines, transcription)
    
    print(f"⏱️  Processing time: {(time.time()-start)/60:.1f} minutes\n")
    
    metadata = {}
    if args.title:
        metadata['title'] = args.title
    if args.artist:
        metadata['artist'] = args.artist
    if args.album:
        metadata['album'] = args.album
    
    LRCWriter.write_lrc(timestamped_lyrics, output_lrc, metadata)
    
    if not args.lrc_only:
        if VideoCreator.create_video(args.audio, output_lrc, output_video,
                                     args.bg_color, args.text_color):
            print(f"\n{'='*60}")
            print("✓ ALL DONE!")
            print(f"{'='*60}")
            print(f"📹 Video: {output_video}")
            print(f"📄 LRC: {output_lrc}")
            
            print(f"\n💡 To adjust timing:")
            print(f"  Edit parameters at top of script, or use:")
            print(f"  --threshold 50-80 (lower=more matches)")
            print(f"  --offset ±seconds (shift all lyrics)")
            print(f"  --speed 0.9-1.1 (adjust pacing)")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted")
        sys.exit(1)
