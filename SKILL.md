---
name: statsfm
description: Query stats.fm (Spotify listening stats) via the public REST API. Provides music listening data, Spotify stats, top artists/tracks/albums, currently playing, streaming history, genre breakdowns, and music taste analysis. No auth needed for public profiles.
---

# stats.fm CLI

Comprehensive Python CLI for querying stats.fm API (Spotify listening analytics).

**Requirements:** Python 3.6+ (stdlib only, no pip installs needed)

**Script location:** `scripts/statsfm.py` in this skill's directory. Examples use `./statsfm.py` assuming you're in the scripts folder.

## Prerequisites

**Stats.fm account (free)**
- Don't have one? Visit [stats.fm](https://stats.fm) and sign up with Spotify or Apple Music (AM untested, Plus status unknown)
- Already have one? Copy your username from your profile
- Supports Spotify and Apple Music

## Setup

Pass your username with `--user USERNAME` / `-u USERNAME`. If no user is provided, the script exits with code 1.

## Quick Start

```bash
# View your profile
./statsfm.py profile

# Top tracks this month
./statsfm.py top-tracks --limit 10

# Track stats for 2025
./statsfm.py track-stats 188745898 --start 2025 --end 2026
```

## All Commands

### User Profile
- `profile` - Show user profile and stats.fm membership info

### Top Lists
- `top-tracks` - Your most played tracks
- `top-artists` - Your most played artists
- `top-albums` - Your most played albums
- `top-genres` - Your top music genres

### Current Activity
- `now-playing` (aliases: `now`, `np`) - Currently playing track
- `recent` - Recently played tracks

### Detailed Stats
- `artist-stats <artist_id>` - Detailed stats for specific artist (with monthly breakdown)
- `track-stats <track_id>` - Detailed stats for specific track (with monthly breakdown)
- `album-stats <album_id>` - Detailed stats for specific album (with monthly breakdown)
- `stream-stats` - Overall streaming statistics

### Drill-Down
- `top-tracks-from-artist <artist_id>` - Top tracks from specific artist
- `top-tracks-from-album <album_id>` - Top tracks from specific album
- `top-albums-from-artist <artist_id>` - Top albums from specific artist

### Global Charts
- `charts-top-tracks` - Global top tracks chart
- `charts-top-artists` - Global top artists chart
- `charts-top-albums` - Global top albums chart

### Search
- `search <query>` - Search for artists, tracks, or albums

## Common Flags

### Date Ranges
All stats commands support both predefined ranges and custom dates:

**Predefined ranges:**
- `--range today` - Today only
- `--range weeks` - Last 4 weeks (default)
- `--range months` - Last 6 months
- `--range lifetime` - All time

**Custom date ranges:**
- `--start YYYY` - Start year (e.g., `--start 2025`)
- `--start YYYY-MM` - Start month (e.g., `--start 2025-07`)
- `--start YYYY-MM-DD` - Start date (e.g., `--start 2025-07-15`)
- `--end YYYY[-MM[-DD]]` - End date (same formats)

**Examples:**
```bash
# All of 2025
./statsfm.py top-artists --start 2025 --end 2026

# Just July 2025
./statsfm.py top-tracks --start 2025-07 --end 2025-08

# Q1 2025
./statsfm.py artist-stats 39118 --start 2025-01-01 --end 2025-03-31
```

### Other Flags
- `--limit N` / `-l N` - Limit results (default varies by command)
- `--user USERNAME` / `-u USERNAME` - Specify the stats.fm username to query
- `--no-album` - Hide album names in track listings (albums show by default)

## Usage Examples

### Basic Queries
```bash
# Your top 10 tracks this week (default range)
./statsfm.py top-tracks --limit 10

# Top 10 artists of all time
./statsfm.py top-artists --range lifetime --limit 10

# What's playing now
./statsfm.py now-playing

# Last 15 tracks played
./statsfm.py recent --limit 15
```

### Using Predefined Ranges
```bash
# Today's top tracks
./statsfm.py top-tracks --range today --limit 20

# Last 4 weeks top artists
./statsfm.py top-artists --range weeks --limit 10

# Last 6 months top albums
./statsfm.py top-albums --range months --limit 15

# All-time top genres
./statsfm.py top-genres --range lifetime --limit 10
```

### Custom Date Ranges
```bash
# How many times did I listen to Espresso in 2025?
./statsfm.py track-stats 188745898 --start 2025 --end 2026

# My top artists in summer 2025
./statsfm.py top-artists --start 2025-06 --end 2025-09

# Sabrina Carpenter stats for Q2 2025
./statsfm.py artist-stats 22369 --start 2025-04 --end 2025-07
```

### Deep Dives
```bash
# Search for Madison Beer
./statsfm.py search "madison beer" --type artist
# Returns: [39118] Madison Beer [pop]

# Get her detailed stats with monthly breakdown
./statsfm.py artist-stats 39118 --start 2025

# See your top tracks from her
./statsfm.py top-tracks-from-artist 39118 --limit 20

# Check a specific album's stats
./statsfm.py album-stats 16211936 --start 2025
```

### Charts
```bash
# What's hot globally today?
./statsfm.py charts-top-tracks --limit 20

# Top albums over the last 6 months
./statsfm.py charts-top-albums --range months --limit 15

# Top artists this week
./statsfm.py charts-top-artists --range weeks
```

### Hide Album Names
```bash
# Compact view without album names
./statsfm.py top-tracks --no-album --limit 10
./statsfm.py recent --no-album
```

## Output Features

### Automatic Monthly Breakdowns
Stats commands (`artist-stats`, `track-stats`, `album-stats`) automatically show:
- Total plays and listening time
- Monthly breakdown with plays and time per month
- Works for both predefined ranges and custom date ranges

Example output:
```
Total: 505 plays  (29h 53m)

Monthly breakdown:
  2025-02:   67 plays  (3h 52m)
  2025-03:  106 plays  (6h 21m)
  2025-04:   40 plays  (2h 24m)
  ...
```

### Display Information
- **Track listings:** Show position, track name, artist, album (by default), play count, time
- **Album listings:** Show position, album name, artist, play count, time
- **Artist listings:** Show position, artist name, play count, time, genres
- **Charts:** Show global rankings with stream counts
- **Recent streams:** Show timestamp, track, artist, album (by default)

## Plus vs Free Users

**Stats.fm Plus required for:**
- Stream counts in top lists
- Listening time (play duration)
- Detailed statistics

**Free users get:**
- Rankings/positions
- Track/artist/album names
- Currently playing
- Search functionality
- Monthly breakdowns (via per-day stats endpoint)

The script handles both gracefully, showing `[Plus required]` for missing data.

## API Information

**Base URL:** `https://api.stats.fm/api/v1`

**Authentication:** None needed for public profiles

**Response format:** JSON with `item` (single) or `items` (list) wrapper

**Rate limiting:** Be reasonable with requests. Avoid more than ~10 calls in rapid succession during deep dives.

## Error Handling

All errors print to **stderr** and exit with **code 1**.

| Scenario | stderr output | What to do |
|----------|--------------|------------|
| No user set | `Error: No user specified.` | Pass `--user USERNAME` flag |
| API error (4xx/5xx) | `API Error (code): message` | Check if user exists, profile is public, or ID is valid |
| Connection failure | `Connection Error: reason` | Retry after a moment, check network |
| Empty results | No error, just no output | User may be private, or no data for that period — try `--range lifetime` |
| Plus-only data | Shows `[Plus required]` inline | Acknowledge gracefully, show what's available |

## Finding IDs

Use search to find artist/track/album IDs:

```bash
# Find artist
./statsfm.py search "sabrina carpenter" --type artist
# Returns: [22369] Sabrina Carpenter [pop]

# Find track
./statsfm.py search "espresso" --type track
# Returns: [188745898] Espresso by Sabrina Carpenter

# Find album
./statsfm.py search "short n sweet" --type album
# Returns: [56735245] Short n' Sweet by Sabrina Carpenter
```

Then use the ID numbers in other commands.

## Tips

1. **Use custom dates for analysis:** `--start 2025 --end 2026` to see full year stats
2. **Chain discoveries:** Search → Get ID → Detailed stats → Drill down
3. **Compare periods:** Run same command with different date ranges
4. **Export data:** Pipe output to file for records: `./statsfm.py top-tracks --start 2025 > 2025_top_tracks.txt`
5. **Albums show by default:** Match the stats.fm UI behavior (album art is prominent)
6. **Monthly breakdowns:** All stats commands show month-by-month progression automatically

## Tips for AI Agents

### Quick Reference — Intent → Command

| User wants | Command | Key flags |
|-----------|---------|-----------|
| Play count for a track | `track-stats <id>` | `--start/--end` for period |
| Play count for an artist | `artist-stats <id>` | `--start/--end` for period |
| Rankings / top lists | `top-tracks`, `top-artists`, `top-albums`, `top-genres` | `--range` or `--start/--end`, `--limit` |
| What's playing now | `now-playing` | |
| Recent listening | `recent` | `--limit` |
| Timeline / listening history | `artist-stats` or `track-stats` | Monthly breakdown is automatic |
| Find an artist/track/album ID | `search <query>` | `--type artist\|track\|album` |
| Deep dive on an artist | `search` → `artist-stats` → `top-tracks-from-artist` | Chain commands |
| Global charts | `charts-top-tracks`, `charts-top-artists` | `--range`, `--limit` |

### Before first use

1. Check memory for a previously stored username
2. If not found, ask the user for their stats.fm username
3. Pass it via `--user USERNAME` when needed

### Workflow patterns

1. **Discovery → Deep dive:** `search` → get ID → `artist-stats` → `top-tracks-from-artist` → specific `track-stats`
2. **Timeline analysis:** Use monthly breakdowns from stats commands to trace listening evolution
3. **Comparison:** Run same command with different date ranges to show changes over time
4. **Era detection:** Check monthly stats for sudden spikes — indicates when an artist entered heavy rotation

### Best practices

- Use custom date ranges (`--start/--end`) for specific periods — more precise than predefined ranges
- When user says "this year" or a specific year, convert to `--start YYYY --end YYYY+1`
- Monthly breakdowns are automatic on stats commands — use them to identify peaks and trends
- Always `search` first to get IDs — don't memorize or hardcode artist/track IDs
- Albums show by default in track listings — use `--no-album` for compact output

### Interpreting patterns

These patterns commonly appear in listening data:

- **Heavy rotation:** Sustained high monthly play counts over multiple months
- **Spike/drop:** Sudden increase followed by decline — often indicates album release or trend
- **Displacement:** One artist's numbers drop as another's rise — taste shift
- **Deep catalog:** Older album tracks appearing in recent top plays — discography exploration
- **Gateway track:** First track in timeline that led to broader artist discovery

### Presenting data

- Highlight peaks and trends in monthly breakdowns
- Contextualize: convert minutes to hours, compare to daily averages
- Show progression across periods when relevant
- Call out notable facts: high single-month counts, rapid rises

### Edge cases

- Free users see `[Plus required]` for play counts — acknowledge gracefully, show what's available
- Some searches return duplicates — use the first result
- Empty results may mean private profile or no data for that period — try `--range lifetime` as fallback
- Apple Music support is untested

## Contributing

Found a bug or want to add a command? Contributions are welcome — open an issue or PR at https://github.com/Beat-YT/statsfm-cli

## References

- API Endpoints: [references/api.md](references/api.md)
- Official JS Client: [statsfm/statsfm.js](https://github.com/statsfm/statsfm.js)
