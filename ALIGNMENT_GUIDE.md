# Understanding the Alignment Code

## What Those Lines Do:

```python
for line in lyrics_lines:
    stripped = line.strip()
    
    # CASE 1: Empty Lines
    if not stripped:
        if timestamped_lyrics:
            timestamped_lyrics.append((timestamped_lyrics[-1][0] + 0.5, ""))
        continue
```
**Explanation:** 
- If the line is empty (blank line in your lyrics file)
- Add it 0.5 seconds after the previous line
- This creates breathing room between sections

```python
    # CASE 2: Section Headers (Verse 1:, Chorus:, etc.)
    if self._is_section_header(stripped):
        if timestamped_lyrics:
            timestamped_lyrics.append((timestamped_lyrics[-1][0] + 1.0, stripped))
        else:
            timestamped_lyrics.append((0.0, stripped))
        continue
```
**Explanation:**
- If the line is a section header like "Verse 1:" or "Chorus:"
- Add it 1.0 seconds after the previous line (gives more space for headers)
- If it's the first line, put it at 0.0 seconds

```python
    # CASE 3: Actual Lyrics
    if content_idx < len(timestamped_content):
        timestamp, _ = timestamped_content[content_idx]
        timestamped_lyrics.append((timestamp, stripped))
        content_idx += 1
```
**Explanation:**
- This is for actual lyric lines (not headers or empty lines)
- Get the timestamp that was calculated earlier
- Add the lyric with its timestamp

---

## Adjustable Parameters and How They Affect Alignment:

### 1. **MATCHING THRESHOLD** (Line ~340)
```python
if best_match and best_match['score'] > 60:  # ← THIS NUMBER
    anchors.append((line_idx, best_match[1]))
```
- **Current:** 60 (accepts matches with 60%+ similarity)
- **Lower (50-55):** More matches, but some may be wrong → better coverage, less accuracy
- **Higher (70-80):** Fewer matches, but more accurate → less coverage, more accuracy
- **Recommended:** 60-65 for most songs

### 2. **SEARCH WINDOW** (Line ~315)
```python
window_seconds=30  # ← THIS NUMBER
```
- **Current:** 30 seconds (searches ±30 seconds from expected position)
- **Larger (40-50):** Can find lyrics further from expected position → good for songs with long instrumentals
- **Smaller (20-25):** Faster processing, but might miss lyrics in unexpected places

### 3. **EMPTY LINE SPACING** (Line shown above)
```python
timestamped_lyrics.append((timestamped_lyrics[-1][0] + 0.5, ""))  # ← 0.5
```
- **Current:** 0.5 seconds after previous line
- **Increase (1.0-2.0):** More space between sections
- **Decrease (0.2-0.3):** Tighter spacing

### 4. **SECTION HEADER SPACING**
```python
timestamped_lyrics.append((timestamped_lyrics[-1][0] + 1.0, stripped))  # ← 1.0
```
- **Current:** 1.0 seconds after previous line
- **Increase (2.0-3.0):** More prominent section breaks
- **Decrease (0.5):** Section headers appear sooner

### 5. **ANCHOR POINT FREQUENCY** (Line ~280)
```python
for line_idx in range(0, len(content_lines), 3):  # ← THIS NUMBER
```
- **Current:** 3 (checks every 3rd line for anchors)
- **Lower (2):** More anchor points → better accuracy, slower processing
- **Higher (4-5):** Fewer anchor points → faster, but may drift more

### 6. **SCORE CALCULATION WEIGHTS** (Line ~330)
```python
score = score * (0.6 + 0.4 * overlap)  # ← THESE NUMBERS
```
- **Current:** 60% base score + 40% word overlap bonus
- **More overlap weight (0.5 + 0.5):** Prioritizes exact word matches
- **Less overlap weight (0.7 + 0.3):** Prioritizes overall similarity

---

## Common Adjustments for Different Situations:

### If lyrics appear TOO EARLY:
```python
# Add a global offset at the end of interpolation
timestamp = start_time + (j * time_per_line) + 0.5  # Add 0.5s offset
```

### If lyrics appear TOO LATE:
```python
# Subtract a global offset
timestamp = start_time + (j * time_per_line) - 0.5  # Subtract 0.5s offset
```

### If lyrics drift over time (get progressively off):
```python
# Adjust the time_per_line calculation
time_per_line = (end_time - start_time) / num_lines * 1.05  # 5% slower
# or
time_per_line = (end_time - start_time) / num_lines * 0.95  # 5% faster
```

### If some sections are good but others are bad:
- Lower the matching threshold (60 → 50) to get more anchor points
- Increase search window (30 → 40) to find matches further away

---

## Quick Reference Table:

| Parameter | Location | Default | Adjust For Better... |
|-----------|----------|---------|---------------------|
| Match threshold | Line ~340 | 60 | Coverage ↓, Accuracy ↑ |
| Search window | Line ~315 | 30 | Finding distant matches ↑ |
| Empty line gap | Line shown | 0.5s | Section spacing ↑/↓ |
| Header gap | Line shown | 1.0s | Header prominence ↑/↓ |
| Anchor frequency | Line ~280 | Every 3 | Accuracy ↑ (lower number) |
| Word overlap weight | Line ~330 | 40% | Exact matching ↑ (higher %) |

---

## Example: Making a More Aggressive Matcher

If your lyrics aren't matching well, try these changes:

```python
# 1. Lower threshold (line ~340)
if best_match and best_match['score'] > 50:  # Was 60

# 2. Check more lines for anchors (line ~280)
for line_idx in range(0, len(content_lines), 2):  # Was 3

# 3. Wider search window (line ~315)
window_seconds=40  # Was 30

# 4. More weight to word overlap (line ~330)
score = score * (0.5 + 0.5 * overlap)  # Was 0.6 + 0.4
```

---

## Example: Adding a Global Time Offset

If EVERYTHING is 2 seconds too early:

```python
# In the _rebuild_with_headers function, add:
if content_idx < len(timestamped_content):
    timestamp, _ = timestamped_content[content_idx]
    timestamp += 2.0  # Add 2 second offset to ALL lyrics
    timestamped_lyrics.append((timestamp, stripped))
    content_idx += 1
```
