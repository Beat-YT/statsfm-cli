#!/usr/bin/env python3
"""
stats.fm CLI - Query stats.fm API for Spotify listening statistics
Usage: statsfm.py <command> [args...]
"""

import sys
import json
import argparse
import os
import time
from typing import Optional, Dict, Any
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from datetime import datetime


BASE_URL = "https://api.stats.fm/api/v1"
DEFAULT_USER = os.environ.get("STATSFM_USER", "")
DEFAULT_RANGE = "weeks"
DEFAULT_LIMIT = 15


class StatsAPI:
    """stats.fm API client"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def request(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the API"""
        url = f"{self.base_url}{endpoint}"

        try:
            req = Request(url)
            req.add_header('User-Agent', 'statsfm-cli/1.0')
            req.add_header('Accept', 'application/json')

            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            try:
                error_data = json.loads(error_body)
                message = error_data.get("message", str(e))
            except json.JSONDecodeError:
                message = str(e)

            print(f"API Error ({e.code}): {message}", file=sys.stderr)
            sys.exit(1)
        except URLError as e:
            print(f"Connection Error: {e.reason}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def format_duration(ms: int) -> str:
    """Format milliseconds as MM:SS"""
    seconds = ms // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


def format_time(ms: int) -> str:
    """Format milliseconds as minutes or hours"""
    mins = ms // 60000
    if mins >= 60:
        hours = mins // 60
        remaining_mins = mins % 60
        return f"{hours:,}h {remaining_mins}m"
    return f"{mins:,} min"


def get_user_or_exit(args) -> str:
    """Get user from args or env, exit if not found"""
    user = args.user or DEFAULT_USER
    if not user:
        print("Error: No user specified. Set STATSFM_USER or pass --user", file=sys.stderr)
        sys.exit(1)
    return user


def get_per_day_stats_with_totals(api: StatsAPI, endpoint: str) -> tuple[Dict[str, Any], int, int]:
    """Get per-day stats and calculate totals"""
    data = api.request(endpoint)
    days = data.get("items", {}).get("days", {})

    total_count = sum(day.get('count', 0) for day in days.values())
    total_ms = sum(day.get('durationMs', 0) for day in days.values())

    return days, total_count, total_ms


def show_monthly_breakdown(days_data: Dict[str, Any], limit: Optional[int] = None):
    """Display monthly breakdown from per-day stats"""
    from collections import defaultdict

    # Group by month
    monthly = defaultdict(lambda: {'count': 0, 'durationMs': 0})

    for date_str, stats in days_data.items():
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            month_key = dt.strftime("%Y-%m")
            monthly[month_key]['count'] += stats['count']
            monthly[month_key]['durationMs'] += stats['durationMs']
        except:
            continue

    # Sort by month and get only months with plays
    months_with_plays = [(month, stats) for month, stats in sorted(monthly.items()) if stats['count'] > 0]

    # Apply limit (most recent months)
    if limit and limit > 0:
        months_with_plays = months_with_plays[-limit:]

    # Display
    print("Monthly breakdown:")
    for month, stats in months_with_plays:
        print(f"  {month}: {stats['count']:>4} plays  ({format_time(stats['durationMs'])})")


def parse_date(date_str: str) -> int:
    """Parse date string to Unix timestamp in milliseconds

    Supports formats:
    - YYYY (e.g., "2025" -> Jan 1, 2025 00:00:00)
    - YYYY-MM (e.g., "2025-06" -> Jun 1, 2025 00:00:00)
    - YYYY-MM-DD (e.g., "2025-06-15" -> Jun 15, 2025 00:00:00)
    """
    parts = date_str.split("-")
    if len(parts) == 1:  # YYYY
        dt = datetime(int(parts[0]), 1, 1)
    elif len(parts) == 2:  # YYYY-MM
        dt = datetime(int(parts[0]), int(parts[1]), 1)
    elif len(parts) == 3:  # YYYY-MM-DD
        dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    else:
        raise ValueError(f"Invalid date format: {date_str}")

    return int(dt.timestamp() * 1000)


def get_album_name(track: dict, max_length: int = 30) -> str:
    """Extract album name from track object"""
    albums = track.get("albums", [])
    if albums:
        return albums[0]["name"][:max_length]
    return "?"


def format_artists(artists: list, max_length: int = None) -> str:
    """Format artist list as comma-separated string"""
    if not artists:
        return "?"
    names = ", ".join(a.get("name", "?") for a in artists)
    if max_length:
        return names[:max_length]
    return names


def build_date_params(args, default_range: str = "weeks") -> str:
    """Build date query parameters from args (range or start/end)

    Returns query string like "range=weeks" or "after=123&before=456"
    """
    if hasattr(args, 'start') and args.start:
        # Use custom date range
        after = parse_date(args.start)
        params = f"after={after}"
        if hasattr(args, 'end') and args.end:
            before = parse_date(args.end)
            params += f"&before={before}"
        return params
    else:
        # Use predefined range
        range_val = args.range if hasattr(args, 'range') and args.range else default_range
        return f"range={range_val}"


def cmd_profile(api: StatsAPI, args):
    """Show user profile"""
    user = get_user_or_exit(args)
    data = api.request(f"/users/{user}")
    u = data.get("item", {})

    name = u.get("displayName", "?")
    pronouns = u.get("profile", {}).get("pronouns", "")
    bio = u.get("profile", {}).get("bio", "")
    plus = " ✓ Plus" if u.get("isPlus") else ""
    created = u.get("createdAt", "")[:10]

    print(f"{name} ({pronouns}){plus}")
    if bio:
        print(f"Bio: {bio}")
    print(f"Member since: {created}")


def cmd_top_artists(api: StatsAPI, args):
    """Show top artists"""
    user = args.user or DEFAULT_USER
    if not user:
        print("Error: No user specified. Set STATSFM_USER or pass --user", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args)
    limit = args.limit or DEFAULT_LIMIT

    data = api.request(f"/users/{user}/top/artists?{date_params}&limit={limit}")
    items = data.get("items", [])

    if not items:
        print("No data found.")
        return

    for item in items:
        pos = item["position"]
        streams = item.get("streams") or "?"
        played_ms = item.get("playedMs", 0)
        artist = item["artist"]
        name = artist["name"][:20]
        genres = ", ".join(artist.get("genres", [])[:2])

        if played_ms and streams != "?":
            print(f"{pos:>3}. {name:<20} {streams:>6} plays ({format_time(played_ms) + ')':<9} [{genres}]")
        else:
            print(f"{pos:>3}. {name:<20} [Plus required for stream stats]  [{genres}]")


def cmd_top_tracks(api: StatsAPI, args):
    """Show top tracks"""
    user = args.user or DEFAULT_USER
    if not user:
        print("Error: No user specified. Set STATSFM_USER or pass --user", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args)
    limit = args.limit or DEFAULT_LIMIT

    data = api.request(f"/users/{user}/top/tracks?{date_params}&limit={limit}")
    items = data.get("items", [])

    if not items:
        print("No data found.")
        return

    for item in items:
        pos = item["position"]
        streams = item.get("streams") or "?"
        played_ms = item.get("playedMs", 0)
        track = item["track"]
        name = track["name"][:35]
        artist = track["artists"][0]["name"][:25]

        if not args.album:
            # Hide album
            if played_ms and streams != "?":
                print(f"{pos:>3}. {name:<35} {artist:<25} {streams:>5} plays  ({format_time(played_ms)})")
            else:
                print(f"{pos:>3}. {name:<35} {artist:<25} [Plus required]")
        else:
            # Show album (default)
            album = get_album_name(track)
            if played_ms and streams != "?":
                print(f"{pos:>3}. {name:<35} {artist:<25} {album:<30} {streams:>5} plays  ({format_time(played_ms)})")
            else:
                print(f"{pos:>3}. {name:<35} {artist:<25} {album:<30} [Plus required]")


def cmd_top_albums(api: StatsAPI, args):
    """Show top albums"""
    user = args.user or DEFAULT_USER
    if not user:
        print("Error: No user specified. Set STATSFM_USER or pass --user", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args)
    limit = args.limit or DEFAULT_LIMIT

    data = api.request(f"/users/{user}/top/albums?{date_params}&limit={limit}")
    items = data.get("items", [])

    if not items:
        print("No data found.")
        return

    for item in items:
        pos = item["position"]
        streams = item.get("streams") or "?"
        played_ms = item.get("playedMs", 0)
        album = item["album"]
        name = album["name"][:35]
        artists = album.get("artists", [])
        artist = artists[0]["name"][:25] if artists else "?"

        if played_ms and streams != "?":
            print(f"{pos:>3}. {name:<35} {artist:<25} {streams:>6} plays  ({format_time(played_ms)})")
        else:
            print(f"{pos:>3}. {name:<35} {artist:<25} [Plus required]")


def cmd_top_genres(api: StatsAPI, args):
    """Show top genres"""
    user = args.user or DEFAULT_USER
    if not user:
        print("Error: No user specified. Set STATSFM_USER or pass --user", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args)
    limit = args.limit or DEFAULT_LIMIT

    data = api.request(f"/users/{user}/top/genres?{date_params}&limit={limit}")
    items = data.get("items", [])

    if not items:
        print("No data found.")
        return

    for item in items:
        pos = item["position"]
        streams = item.get("streams") or "?"
        played_ms = item.get("playedMs", 0)
        genre = item["genre"]
        tag = genre["tag"][:40]

        if played_ms and streams != "?":
            print(f"{pos:>3}. {tag:<40} {streams:>6} plays  ({format_time(played_ms)})")
        else:
            print(f"{pos:>3}. {tag:<40} [Plus required]")


def cmd_now_playing(api: StatsAPI, args):
    """Show currently playing track"""
    user = args.user or DEFAULT_USER
    if not user:
        print("Error: No user specified. Set STATSFM_USER or pass --user", file=sys.stderr)
        sys.exit(1)

    data = api.request(f"/users/{user}/streams/current")
    item = data.get("item")

    if not item:
        print("Nothing playing.")
        return

    track = item["track"]
    artists = format_artists(track["artists"])
    name = track["name"]
    album = track["albums"][0]["name"] if track.get("albums") else "?"
    progress = item["progressMs"] // 1000
    duration = track["durationMs"] // 1000
    device = item.get("deviceName", "?")
    icon = "▶" if item.get("isPlaying") else "⏸"
    track_id = track.get("id", "?")
    artist_id = track["artists"][0].get("id", "?") if track.get("artists") else "?"

    print(f"{icon} {artists} — {name}")
    print(f"   Album: {album}")
    print(f"   {progress//60}:{progress%60:02d} / {duration//60}:{duration%60:02d}  •  {device}")
    print(f"   IDs: track={track_id}, artist={artist_id}")


def cmd_recent(api: StatsAPI, args):
    """Show recently played tracks"""
    user = args.user or DEFAULT_USER
    if not user:
        print("Error: No user specified. Set STATSFM_USER or pass --user", file=sys.stderr)
        sys.exit(1)

    limit = args.limit or 10

    data = api.request(f"/users/{user}/streams/recent?limit={limit}")
    items = data.get("items", [])

    if not items:
        print("No recent streams found.")
        return

    for stream in items:
        track = stream.get("track", {})
        name = track.get("name", "?")[:35]
        artist = track.get("artists", [{}])[0].get("name", "?")[:25]
        end_time = stream.get("endTime", "")

        if end_time:
            try:
                dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except:
                time_str = "??:??"
        else:
            time_str = "??:??"

        if not args.album:
            # Hide album
            print(f"  {time_str}  {name:<35} {artist:<25}")
        else:
            # Show album (default)
            album = get_album_name(track)
            print(f"  {time_str}  {name:<35} {artist:<25} {album:<30}")


def cmd_artist_stats(api: StatsAPI, args):
    """Show stats for a specific artist"""
    user = get_user_or_exit(args)

    if not args.artist_id:
        print("Error: Artist ID required", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args, "lifetime")
    days, total_count, total_ms = get_per_day_stats_with_totals(
        api, f"/users/{user}/streams/artists/{args.artist_id}/stats/per-day?timeZone=UTC&{date_params}"
    )

    print(f"Total: {total_count} plays  ({format_time(total_ms)})")
    print()
    show_monthly_breakdown(days, getattr(args, 'limit', None))


def cmd_track_stats(api: StatsAPI, args):
    """Show stats for a specific track"""
    user = get_user_or_exit(args)

    if not args.track_id:
        print("Error: Track ID required", file=sys.stderr)
        sys.exit(1)

    # Fetch track info
    track_data = api.request(f"/tracks/{args.track_id}")
    track = track_data.get("item", {})
    track_name = track.get("name", "?")
    artists = format_artists(track.get("artists", []))
    album = get_album_name(track) if track.get("albums") else "?"

    print(f"{track_name} by {artists}")
    print(f"Album: {album}")
    print()

    date_params = build_date_params(args, "lifetime")
    days, total_count, total_ms = get_per_day_stats_with_totals(
        api, f"/users/{user}/streams/tracks/{args.track_id}/stats/per-day?timeZone=UTC&{date_params}"
    )

    print(f"Total: {total_count} plays  ({format_time(total_ms)})")
    print()
    show_monthly_breakdown(days, getattr(args, 'limit', None))


def cmd_album_stats(api: StatsAPI, args):
    """Show stats for a specific album"""
    user = get_user_or_exit(args)

    if not args.album_id:
        print("Error: Album ID required", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args, "lifetime")
    days, total_count, total_ms = get_per_day_stats_with_totals(
        api, f"/users/{user}/streams/albums/{args.album_id}/stats/per-day?timeZone=UTC&{date_params}"
    )

    print(f"Total: {total_count} plays  ({format_time(total_ms)})")
    print()
    show_monthly_breakdown(days, getattr(args, 'limit', None))


def cmd_stream_stats(api: StatsAPI, args):
    """Show overall stream statistics"""
    user = args.user or DEFAULT_USER
    if not user:
        print("Error: No user specified. Set STATSFM_USER or pass --user", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args)

    data = api.request(f"/users/{user}/streams/stats?{date_params}")
    items = data.get("items", data.get("item", {}))

    if isinstance(items, dict):
        # Display overall stats
        count = items.get("count", items.get("streams", "?"))
        ms = items.get("durationMs", items.get("playedMs", 0))

        print(f"Total Streams: {count}")
        print(f"Total Time: {format_time(ms)}")

        # Additional stats if available
        if "cardsCount" in items:
            print(f"Unique Tracks: {items['cardsCount']}")
        if "hoursStreamed" in items:
            print(f"Hours Streamed: {items['hoursStreamed']:.1f}")
    else:
        print(json.dumps(items, indent=2))


def cmd_top_tracks_from_artist(api: StatsAPI, args):
    """Show top tracks from a specific artist"""
    user = get_user_or_exit(args)

    if not args.artist_id:
        print("Error: Artist ID required", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args)
    limit = args.limit or DEFAULT_LIMIT

    data = api.request(f"/users/{user}/top/artists/{args.artist_id}/tracks?{date_params}&limit={limit}")
    items = data.get("items", [])

    if not items:
        print("No data found.")
        return

    for item in items:
        pos = item["position"]
        streams = item.get("streams") or "?"
        played_ms = item.get("playedMs", 0)
        track = item["track"]
        name = track["name"][:40]

        if not args.album:
            # Hide album
            if played_ms and streams != "?":
                print(f"{pos:>3}. {name:<40} {streams:>5} plays  ({format_time(played_ms)})")
            else:
                print(f"{pos:>3}. {name:<40} [Plus required]")
        else:
            # Show album (default)
            album = get_album_name(track)
            if played_ms and streams != "?":
                print(f"{pos:>3}. {name:<40} {album:<30} {streams:>5} plays  ({format_time(played_ms)})")
            else:
                print(f"{pos:>3}. {name:<40} {album:<30} [Plus required]")


def cmd_top_tracks_from_album(api: StatsAPI, args):
    """Show top tracks from a specific album"""
    user = get_user_or_exit(args)

    if not args.album_id:
        print("Error: Album ID required", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args)
    limit = args.limit or DEFAULT_LIMIT

    data = api.request(f"/users/{user}/top/albums/{args.album_id}/tracks?{date_params}&limit={limit}")
    items = data.get("items", [])

    if not items:
        print("No data found.")
        return

    for item in items:
        pos = item["position"]
        streams = item.get("streams") or "?"
        played_ms = item.get("playedMs", 0)
        track = item["track"]
        name = track["name"][:40]

        if played_ms and streams != "?":
            print(f"{pos:>3}. {name:<40} {streams:>5} plays  ({format_time(played_ms)})")
        else:
            print(f"{pos:>3}. {name:<40} [Plus required]")


def cmd_top_albums_from_artist(api: StatsAPI, args):
    """Show top albums from a specific artist"""
    user = get_user_or_exit(args)

    if not args.artist_id:
        print("Error: Artist ID required", file=sys.stderr)
        sys.exit(1)

    date_params = build_date_params(args)
    limit = args.limit or DEFAULT_LIMIT

    data = api.request(f"/users/{user}/top/artists/{args.artist_id}/albums?{date_params}&limit={limit}")
    items = data.get("items", [])

    if not items:
        print("No data found.")
        return

    for item in items:
        pos = item["position"]
        streams = item.get("streams") or "?"
        played_ms = item.get("playedMs", 0)
        album = item["album"]
        name = album["name"][:40]

        if played_ms and streams != "?":
            print(f"{pos:>3}. {name:<40} {streams:>5} plays  ({format_time(played_ms)})")
        else:
            print(f"{pos:>3}. {name:<40} [Plus required]")


def cmd_charts_top_tracks(api: StatsAPI, args):
    """Show global top tracks chart"""
    range_val = args.range or "today"
    limit = args.limit or 15

    data = api.request(f"/charts/top/tracks?range={range_val}")
    items = data.get("items", [])[:limit]  # Apply limit in software

    if not items:
        print("No chart data found.")
        return

    print(f"Global Top Tracks ({range_val}):")
    for item in items:
        pos = item.get("position", "?")
        streams = item.get("streams", 0)
        track = item.get("track", {})
        name = track.get("name", "?")[:40]
        artists = track.get("artists", [])
        artist = artists[0].get("name", "?")[:25] if artists else "?"

        if not args.album:
            # Hide album
            print(f"{pos:>3}. {name:<40} {artist:<25} {streams:>8} streams")
        else:
            # Show album (default)
            album = get_album_name(track)
            print(f"{pos:>3}. {name:<40} {artist:<25} {album:<30} {streams:>8} streams")


def cmd_charts_top_artists(api: StatsAPI, args):
    """Show global top artists chart"""
    range_val = args.range or "today"
    limit = args.limit or 15

    data = api.request(f"/charts/top/artists?range={range_val}")
    items = data.get("items", [])[:limit]  # Apply limit in software

    if not items:
        print("No chart data found.")
        return

    print(f"Global Top Artists ({range_val}):")
    for item in items:
        pos = item.get("position", "?")
        streams = item.get("streams", 0)
        artist = item.get("artist", {})
        name = artist.get("name", "?")[:40]
        genres = ", ".join(artist.get("genres", [])[:2])

        print(f"{pos:>3}. {name:<40} {streams:>8} streams  [{genres}]")


def cmd_charts_top_albums(api: StatsAPI, args):
    """Show global top albums chart"""
    range_val = args.range or "today"
    limit = args.limit or 15

    data = api.request(f"/charts/top/albums?range={range_val}")
    items = data.get("items", [])[:limit]  # Apply limit in software

    if not items:
        print("No chart data found.")
        return

    print(f"Global Top Albums ({range_val}):")
    for item in items:
        pos = item.get("position", "?")
        streams = item.get("streams", 0)
        album = item.get("album", {})
        name = album.get("name", "?")[:40]
        artists = album.get("artists", [])
        artist = artists[0].get("name", "?")[:30] if artists else "?"

        print(f"{pos:>3}. {name:<40} {artist:<30} {streams:>8} streams")


def cmd_search(api: StatsAPI, args):
    """Search for artists, tracks, or albums"""
    if not args.query:
        print("Error: Search query required", file=sys.stderr)
        sys.exit(1)

    search_type = args.type
    limit = args.limit or 5
    encoded_query = quote(args.query)

    # Build URL: omit type param for broad search across all categories
    if search_type:
        url = f"/search?query={encoded_query}&type={search_type}&limit={limit}"
    else:
        url = f"/search?query={encoded_query}&limit={limit}"

    data = api.request(url)
    items = data.get("items", {})

    found_any = False

    # Show artists if type is artist or broad search
    if search_type in ("artist", None):
        artists = items.get("artists", [])
        if artists:
            found_any = True
            print("\nARTISTS:")
            for artist in artists[:limit]:
                aid = artist.get("id", "?")
                name = artist.get("name", "?")
                genres = ", ".join(artist.get("genres", [])[:2])
                extra = f"  [{genres}]" if genres else ""
                print(f"  [{aid}] {name}{extra}")

    # Show tracks if type is track or broad search
    if search_type in ("track", None):
        tracks = items.get("tracks", [])
        if tracks:
            found_any = True
            print("\nTRACKS:")
            for track in tracks[:limit]:
                tid = track.get("id", "?")
                name = track.get("name", "?")
                artists = format_artists(track.get("artists", []))
                print(f"  [{tid}] {name} by {artists}")

    # Show albums if type is album or broad search
    if search_type in ("album", None):
        albums = items.get("albums", [])
        if albums:
            found_any = True
            print("\nALBUMS:")
            for album in albums[:limit]:
                alb_id = album.get("id", "?")
                name = album.get("name", "?")
                artists = format_artists(album.get("artists", []))
                print(f"  [{alb_id}] {name} by {artists}")

    if not found_any:
        print("No results found.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="stats.fm CLI - Query Spotify listening statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s top-artists
  %(prog)s top-tracks --range lifetime --limit 20
  %(prog)s now-playing --user <username>
  %(prog)s search "madison beer"
  %(prog)s search "madison beer" --type artist
  %(prog)s track-stats 70714270 --range lifetime
  %(prog)s album-stats 16211936
  %(prog)s stream-stats --range weeks

Ranges: today, weeks (4 weeks), months (6 months), lifetime
Set STATSFM_USER environment variable for default user
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Show user profile")
    profile_parser.add_argument("--user", "-u", help="stats.fm username")

    # Top artists command
    artists_parser = subparsers.add_parser("top-artists", help="Show top artists")
    artists_parser.add_argument("--range", "-r", help="Time range (default: weeks)")
    artists_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    artists_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    artists_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 10)")
    artists_parser.add_argument("--user", "-u", help="stats.fm username")

    # Top tracks command
    tracks_parser = subparsers.add_parser("top-tracks", help="Show top tracks")
    tracks_parser.add_argument("--range", "-r", help="Time range (default: weeks)")
    tracks_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    tracks_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    tracks_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 10)")
    tracks_parser.add_argument("--user", "-u", help="stats.fm username")
    tracks_parser.add_argument("--no-album", dest="album", action="store_false", help="Hide album name")

    # Top albums command
    albums_parser = subparsers.add_parser("top-albums", help="Show top albums")
    albums_parser.add_argument("--range", "-r", help="Time range (default: weeks)")
    albums_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    albums_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    albums_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 10)")
    albums_parser.add_argument("--user", "-u", help="stats.fm username")

    # Top genres command
    genres_parser = subparsers.add_parser("top-genres", help="Show top genres")
    genres_parser.add_argument("--range", "-r", help="Time range (default: weeks)")
    genres_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    genres_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    genres_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 10)")
    genres_parser.add_argument("--user", "-u", help="stats.fm username")

    # Now playing command
    now_parser = subparsers.add_parser("now-playing", aliases=["now", "np"], help="Show currently playing")
    now_parser.add_argument("--user", "-u", help="stats.fm username")

    # Recent command
    recent_parser = subparsers.add_parser("recent", help="Show recently played tracks")
    recent_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 10)")
    recent_parser.add_argument("--user", "-u", help="stats.fm username")
    recent_parser.add_argument("--no-album", dest="album", action="store_false", help="Hide album name")

    # Artist stats command
    artist_stats_parser = subparsers.add_parser("artist-stats", help="Show stats for a specific artist")
    artist_stats_parser.add_argument("artist_id", help="Artist ID")
    artist_stats_parser.add_argument("--range", "-r", help="Time range (weeks/months/lifetime)")
    artist_stats_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    artist_stats_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    artist_stats_parser.add_argument("--limit", "-l", type=int, help="Limit to most recent N months")
    artist_stats_parser.add_argument("--user", "-u", help="stats.fm username")

    # Track stats command
    track_stats_parser = subparsers.add_parser("track-stats", help="Show stats for a specific track")
    track_stats_parser.add_argument("track_id", type=int, help="Track ID")
    track_stats_parser.add_argument("--range", "-r", help="Time range (weeks/months/lifetime)")
    track_stats_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    track_stats_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    track_stats_parser.add_argument("--limit", "-l", type=int, help="Limit to most recent N months")
    track_stats_parser.add_argument("--user", "-u", help="stats.fm username")

    # Album stats command
    album_stats_parser = subparsers.add_parser("album-stats", help="Show stats for a specific album")
    album_stats_parser.add_argument("album_id", type=int, help="Album ID")
    album_stats_parser.add_argument("--range", "-r", help="Time range (weeks/months/lifetime)")
    album_stats_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    album_stats_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    album_stats_parser.add_argument("--limit", "-l", type=int, help="Limit to most recent N months")
    album_stats_parser.add_argument("--user", "-u", help="stats.fm username")

    # Stream stats command
    stream_stats_parser = subparsers.add_parser("stream-stats", help="Show overall stream statistics")
    stream_stats_parser.add_argument("--range", "-r", help="Time range (default: weeks)")
    stream_stats_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    stream_stats_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    stream_stats_parser.add_argument("--user", "-u", help="stats.fm username")

    # Top tracks from artist command
    top_tracks_artist_parser = subparsers.add_parser("top-tracks-from-artist", help="Show top tracks from a specific artist")
    top_tracks_artist_parser.add_argument("artist_id", help="Artist ID")
    top_tracks_artist_parser.add_argument("--range", "-r", help="Time range (default: weeks)")
    top_tracks_artist_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    top_tracks_artist_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    top_tracks_artist_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 15)")
    top_tracks_artist_parser.add_argument("--user", "-u", help="stats.fm username")
    top_tracks_artist_parser.add_argument("--no-album", dest="album", action="store_false", help="Hide album name")

    # Top tracks from album command
    top_tracks_album_parser = subparsers.add_parser("top-tracks-from-album", help="Show top tracks from a specific album")
    top_tracks_album_parser.add_argument("album_id", type=int, help="Album ID")
    top_tracks_album_parser.add_argument("--range", "-r", help="Time range (default: weeks)")
    top_tracks_album_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    top_tracks_album_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    top_tracks_album_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 15)")
    top_tracks_album_parser.add_argument("--user", "-u", help="stats.fm username")

    # Top albums from artist command
    top_albums_artist_parser = subparsers.add_parser("top-albums-from-artist", help="Show top albums from a specific artist")
    top_albums_artist_parser.add_argument("artist_id", help="Artist ID")
    top_albums_artist_parser.add_argument("--range", "-r", help="Time range (default: weeks)")
    top_albums_artist_parser.add_argument("--start", help="Start date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    top_albums_artist_parser.add_argument("--end", help="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    top_albums_artist_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 15)")
    top_albums_artist_parser.add_argument("--user", "-u", help="stats.fm username")

    # Charts commands
    charts_tracks_parser = subparsers.add_parser("charts-top-tracks", help="Show global top tracks chart")
    charts_tracks_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 15)")
    charts_tracks_parser.add_argument("--range", "-r", help="Time range (default: today)")
    charts_tracks_parser.add_argument("--no-album", dest="album", action="store_false", help="Hide album name")

    charts_artists_parser = subparsers.add_parser("charts-top-artists", help="Show global top artists chart")
    charts_artists_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 15)")
    charts_artists_parser.add_argument("--range", "-r", help="Time range (default: today)")

    charts_albums_parser = subparsers.add_parser("charts-top-albums", help="Show global top albums chart")
    charts_albums_parser.add_argument("--limit", "-l", type=int, help="Number of results (default: 15)")
    charts_albums_parser.add_argument("--range", "-r", help="Time range (default: today)")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for artists, tracks, or albums")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", "-t", choices=["artist", "track", "album"], help="Filter by type (omit to search all)")
    search_parser.add_argument("--limit", "-l", type=int, help="Results per category (default: 5)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    api = StatsAPI()

    # Route to appropriate command
    commands = {
        "profile": cmd_profile,
        "top-artists": cmd_top_artists,
        "top-tracks": cmd_top_tracks,
        "top-albums": cmd_top_albums,
        "top-genres": cmd_top_genres,
        "now-playing": cmd_now_playing,
        "now": cmd_now_playing,
        "np": cmd_now_playing,
        "recent": cmd_recent,
        "artist-stats": cmd_artist_stats,
        "track-stats": cmd_track_stats,
        "album-stats": cmd_album_stats,
        "stream-stats": cmd_stream_stats,
        "top-tracks-from-artist": cmd_top_tracks_from_artist,
        "top-tracks-from-album": cmd_top_tracks_from_album,
        "top-albums-from-artist": cmd_top_albums_from_artist,
        "charts-top-tracks": cmd_charts_top_tracks,
        "charts-top-artists": cmd_charts_top_artists,
        "charts-top-albums": cmd_charts_top_albums,
        "search": cmd_search,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(api, args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
