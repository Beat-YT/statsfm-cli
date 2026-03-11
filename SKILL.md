---
name: statsfm
description: Music data tool powered by the stats.fm API. Look up album tracklists, artist discographies, and global charts without an account. With a stats.fm username, query personal Spotify listening history, play counts, top artists/tracks/albums, monthly breakdowns, and currently playing.
---

# stats.fm Skill

Query Spotify listening data through the stats.fm API. Personal stats, artist deep dives, discovery timelines, discographies, and global charts.

**Script:** `scripts/statsfm.py` (Python 3.6+, stdlib only)

## Setup

Check memory for a stats.fm username. If you don't have one, ask — all personal commands need `--user USERNAME` (`-u`). Public commands (search, album, artist-albums, charts) work without a username.

## How to Be Good at This

This skill is worthless if you call one command and dump the output. Music is personal. When someone asks about an artist or a phase, they want to *feel* something — not read a database query. Your job is to chain multiple calls, find the story in the data, and tell it back.

### The golden rule: never stop at one call

If someone asks "how much do I listen to PinkPantheress," don't just run `artist-stats` and recite numbers. That's a Google search, not a conversation. Instead:

1. `artist-stats` for the big picture — total plays, monthly arc
2. `top-tracks-from-artist` to see which songs carry the obsession
3. `artist-albums` or `album` to add context — is it one album on repeat, or the full catalog?
4. Compare time ranges — is this a current fixation or a slow burn?

Then *synthesize*. "You've played PinkPantheress 340 times since January, but it's not evenly spread — March was massive (89 plays), then it cooled off. 'Boy's a liar Pt. 2' alone accounts for nearly a third of your total. You basically discovered her through that track and branched out from there."

That's the difference between data and insight.

### Workflow patterns

**"Tell me about my [artist] phase"** — the deep dive
```
search "<artist>" --type artist          → get artist ID
artist-stats <id> --range all            → lifetime arc, find when it started
artist-stats <id> --start <peak_year> --end <next_year> --granularity weekly  → week-by-week zoom on the hot period
top-tracks-from-artist <id> --range all  → which songs define the phase
top-albums-from-artist <id> --range all  → album-level view
album <album_id>                         → tracklist for context on their top album
```
Narrative goal: *When did this start, what peaked, what's the signature track, is it still going or fading?*

**"When did I discover [artist]?"** — the origin story
```
search "<artist>" --type artist          → get ID
artist-stats <id> --range all            → monthly breakdown reveals first appearance
track-stats <first_track_id> --range all → confirm the entry point track
top-tracks-from-artist <id> --range all  → show how taste evolved across their catalog
```
Narrative goal: *Pin the exact month, identify the gateway track, show how you went deeper.*

**"What's my [artist] breakdown look like this year?"** — the status check
```
search "<artist>" --type artist (if needed)                       → get artist ID
artist-stats <id> --start <year> --end <next_year>                → year totals + monthly
top-tracks-from-artist <id> --start <year> --end <next_year>      → current favorites
artist-stats <id> --range all                                      → compare to lifetime
```
Narrative goal: *Where does this year rank vs. your history? Accelerating or coasting?*

**"How do I listen to [album]?"** — the album autopsy
```
search "<album>" --type album            → get album ID
album <id>                               → full tracklist
album-stats <id> --range all             → total plays + arc
top-tracks-from-album <id> --range all   → track ranking within the album
top-tracks-from-album <id> --start <year> --end <next_year>  → recent favorites vs. all-time above
```
Narrative goal: *Which tracks carry the album? Do you listen front-to-back or cherry-pick? Still active or nostalgia?*

**"What have I been into lately?"** — the snapshot
```
top-artists --range 7d                   → this week
top-artists --range 30d                  → this month
recent --limit 20                        → raw recent plays for texture
now-playing                              → if they're listening right now, anchor to it
```
Narrative goal: *Paint the current moment. What's dominating? Anything surprising?*

### Voice and tone

- **Be specific, not generic.** "You really like this artist" is worthless. "You've averaged 4 plays a day of this track for two weeks straight" is a story.
- **Notice patterns.** Monthly breakdowns exist for a reason. If there's a spike, a drop-off, a seasonal rhythm — call it out.
- **Use the numbers as scaffolding, not the point.** Don't list every month's play count. Pick the interesting ones and weave them into observations.
- **Compare things.** A number alone means nothing. 200 plays is a lot if they only have 2,000 total streams. It's nothing if they have 50,000. Use `stream-stats` as a denominator when it helps.
- **It's okay to editorialize lightly.** "That's a pretty intense listening run" or "this one clearly didn't stick the same way" — you're having a music conversation, not filing a report.
- **Don't over-explain the tool.** Never say "I'll now run artist-stats to check your monthly breakdown." Just do it. The user doesn't care about your process.

### What NOT to do

- Run one command and present raw output
- List every month in a breakdown when only 2-3 are interesting
- Say "I don't have enough data" without trying `--range all` first
- Prefix every data point with "According to your stats.fm data..." — they know
- Ask the user for an artist ID — search for it yourself
- Apologize for rate limits or missing data — just work with what you get

## Time Range Translations

| User says | You use |
|-----------|---------|
| "this year" / "in 2025" | `--start 2025 --end 2026` |
| "last year" | `--start 2024 --end 2025` |
| "this month" | `--start 2025-03 --end 2025-04` (adjust to current month) |
| "last summer" | `--start 2025-06 --end 2025-09` |
| "lately" / "recently" | `--range 30d` (and maybe compare to `--range all`) |
| "ever" / "all time" | `--range all` |
| "this week" | `--range 7d` |
| "when did I start" | `--range all` then read the monthly breakdown |

## Edge Cases

- **Empty results?** Retry with `--range all` automatically. If still empty, the profile might be private. Mention it briefly and move on.
- **Free (non-Plus) users:** Play counts won't appear in top lists. Rankings and monthly breakdowns still work — lead with those. Don't make a big deal out of missing data.
- **Rate limiting:** Space things out slightly, but don't hold back from 5-7 calls on a deep dive. That's what this skill is for.
- **Search duplicates:** Use the first result unless something looks obviously wrong.
- **No username in memory:** Ask once, remember it. Don't re-ask every conversation.

---

## CLI Reference

Everything below is command-level documentation. The workflows above are how you *should* use these — this section is for looking up flags and syntax when you need them.

### Command Syntax

All commands: `./statsfm.py <command> [args] [flags]`

Global flags for all personal commands: `--user USERNAME` / `-u USERNAME`

### Commands

**Profile & Activity**

| Command | Description |
|---------|-------------|
| `profile` | Username, pronouns, bio, Plus status, Spotify sync info |
| `now-playing` / `np` | Currently playing track |
| `recent` | Recently played tracks |
| `stream-stats` | Overall summary: total streams, time, averages, unique counts |

**Your Top Lists**

| Command | Description | Key flags |
|---------|-------------|-----------|
| `top-tracks` | Most played tracks | `--range`, `--start/--end`, `--limit`, `--no-album` |
| `top-artists` | Most played artists | `--range`, `--start/--end`, `--limit` |
| `top-albums` | Most played albums | `--range`, `--start/--end`, `--limit` |
| `top-genres` | Top genres | `--range`, `--start/--end`, `--limit` |

**Detailed Stats (with breakdowns)**

| Command | Description | Key flags |
|---------|-------------|-----------|
| `artist-stats <id>` | Play count, time, breakdown for an artist | `--start/--end`, `--range`, `--granularity` |
| `track-stats <id>` | Play count, time, breakdown for a track | `--start/--end`, `--range`, `--granularity` |
| `album-stats <id>` | Play count, time, breakdown for an album | `--start/--end`, `--range`, `--granularity` |

**Lookups (no account needed)**

| Command | Description | Key flags |
|---------|-------------|-----------|
| `search <query>` | Find artists, tracks, or albums | `--type artist\|track\|album` |
| `artist <id>` | Artist info, genres, popularity, discography | `--type album\|single\|all`, `--limit` |
| `album <id>` | Album info and full tracklist | |
| `artist-albums <id>` | Discography grouped by type, newest first | `--type album\|single\|all`, `--limit` |

**Drill-Down (your stats within an artist/album)**

| Command | Description | Key flags |
|---------|-------------|-----------|
| `top-tracks-from-artist <id>` | Your most played tracks by this artist | `--range`, `--limit` |
| `top-tracks-from-album <id>` | Your most played tracks on this album | `--range`, `--limit` |
| `top-albums-from-artist <id>` | Your most played albums by this artist | `--range`, `--limit` |

**Global Charts (no account needed)**

| Command | Description | Key flags |
|---------|-------------|-----------|
| `charts-top-tracks` | Global top tracks | `--range`, `--limit` |
| `charts-top-artists` | Global top artists | `--range`, `--limit` |
| `charts-top-albums` | Global top albums | `--range`, `--limit` |

### Date Range Flags

**Predefined:** `--range today`, `1d`, `4w` (default), `6m`, `all`

**Duration:** `--range 7d`, `14d`, `30d`, `90d`

**Custom:** `--start YYYY[-MM[-DD]]` and `--end YYYY[-MM[-DD]]`

### Granularity

`--granularity monthly` (default) | `weekly` | `daily`

Works with `artist-stats`, `track-stats`, `album-stats`.

### Other Flags

| Flag | Description |
|------|-------------|
| `--limit N` / `-l N` | Limit results (default: 15) |
| `--no-album` | Hide album names in track listings |

### Finding IDs

```bash
./statsfm.py search "sabrina carpenter" --type artist
# → [22369] Sabrina Carpenter [pop]

./statsfm.py search "espresso" --type track
# → [188745898] Espresso by Sabrina Carpenter

./statsfm.py search "short n sweet" --type album
# → [56735245] Short n' Sweet by Sabrina Carpenter
```

### Error Handling

| Scenario | Output | Auto-fix |
|----------|--------|----------|
| No user set | `Error: No user specified.` | Ask for username, store in memory |
| API error (4xx/5xx) | `API Error (code): message` | Check if profile is public, ID is valid |
| Empty results | No output | Retry with `--range all` |
| Plus-only data | `[Plus required]` inline | Work with what's available, don't dwell on it |

### API Info

- **Base URL:** `https://api.stats.fm/api/v1`
- **Auth:** None for public profiles
- **Response format:** JSON with `item`/`items` wrapper

### References
- GitHub: [statsfm/statsfm-cli](https://github.com/Beat-YT/statsfm-cli)
- API Endpoints: [references/api.md](references/api.md)
- Official JS Client: [statsfm/statsfm.js](https://github.com/statsfm/statsfm.js)
