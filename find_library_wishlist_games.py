#!/usr/bin/env python3
"""
Find games that are both in your BGG collection CSV export
AND available in the Gen Con Games Library on tabletop.events.
"""

import argparse
import csv
import time
from dataclasses import dataclass
from pathlib import Path

import requests


@dataclass
class Game:
    name: str
    bgg_id: int
    library_catalog_number: str | None = None
    is_checked_out: bool = False
    wishlist_priority: int | None = None  # 1-5, where 1 is highest priority
    want_to_play: bool = False


def fetch_tabletop_events_library() -> dict[int, Game]:
    """Fetch all games from the Gen Con Games Library."""
    library_id = "04AF9CCA-4007-11E7-B936-583CAF0F8503"
    base_url = f"https://tabletop.events/api/library/{library_id}/librarygames"

    games: dict[int, Game] = {}
    page = 1

    print("Fetching Gen Con Games Library...")

    while True:
        params = {
            "_page_number": page,
            "_items_per_page": 100,
            "_include_relationships": 1,
        }

        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        items = data.get("result", {}).get("items", [])
        paging = data.get("result", {}).get("paging", {})

        for item in items:
            bgg_id = item.get("bgg_id")
            if bgg_id:
                games[int(bgg_id)] = Game(
                    name=item.get("name", "Unknown"),
                    bgg_id=int(bgg_id),
                    library_catalog_number=item.get("catalog_number"),
                    is_checked_out=item.get("is_checked_out", False),
                )

        total_pages = paging.get("total_pages", 1)
        print(f"  Page {page}/{total_pages} ({len(games)} games with BGG IDs so far)")

        if page >= total_pages:
            break

        page += 1
        time.sleep(0.1)

    print(f"Found {len(games)} games with BGG IDs in the library.\n")
    return games


@dataclass
class BGGGame:
    name: str
    wishlist_priority: int | None  # 1-5, where 1 is highest priority
    want_to_play: bool


def load_bgg_csv(
    csv_path: Path,
    include_wishlist: bool = True,
    include_want_to_play: bool = True,
) -> dict[int, BGGGame]:
    """
    Load games from a BGG collection CSV export.

    Filters to only include games marked as wishlist or want-to-play.
    Returns a dict mapping BGG ID to BGGGame info.
    """
    games: dict[int, BGGGame] = {}
    wishlist_count = 0
    want_to_play_count = 0

    print(f"Loading BGG games from {csv_path}...")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            bgg_id = row.get("objectid")
            name = row.get("objectname", "Unknown")

            if not bgg_id:
                continue

            is_wishlist = row.get("wishlist") == "1"
            is_want_to_play = row.get("wanttoplay") == "1"
            wishlist_priority = row.get("wishlistpriority")

            if include_wishlist and is_wishlist:
                games[int(bgg_id)] = BGGGame(
                    name=name,
                    wishlist_priority=int(wishlist_priority) if wishlist_priority else None,
                    want_to_play=is_want_to_play,
                )
                wishlist_count += 1
            elif include_want_to_play and is_want_to_play:
                games[int(bgg_id)] = BGGGame(
                    name=name,
                    wishlist_priority=None,  # Not a wishlist item, ignore any priority value
                    want_to_play=True,
                )
                want_to_play_count += 1

    print(f"  Found {wishlist_count} wishlist games, {want_to_play_count} want-to-play games")
    print(f"  Total: {len(games)} unique games\n")
    return games


def find_matching_games(
    library_games: dict[int, Game],
    bgg_games: dict[int, BGGGame],
) -> list[Game]:
    """Find games that appear in both the library and the user's BGG list."""
    matching = []

    for bgg_id, bgg_game in bgg_games.items():
        if bgg_id in library_games:
            game = library_games[bgg_id]
            game.wishlist_priority = bgg_game.wishlist_priority
            game.want_to_play = bgg_game.want_to_play
            matching.append(game)

    # Sort by priority: wishlist tier first (1 is highest), then want-to-play,
    # then alphabetically by name within each tier
    def sort_key(g: Game) -> tuple:
        # Wishlist priority: 1 is highest, None goes last (use 99)
        priority = g.wishlist_priority if g.wishlist_priority else 99
        # Want-to-play without wishlist tier comes after all wishlist tiers
        return (priority, g.name.lower())

    return sorted(matching, key=sort_key)


def main():
    parser = argparse.ArgumentParser(
        description="Find games in both your BGG collection CSV and the Gen Con Games Library."
    )
    parser.add_argument(
        "--csv",
        default="bgg_games.csv",
        help="Path to your BGG collection CSV export (default: bgg_games.csv)",
    )
    parser.add_argument(
        "--wishlist-only",
        action="store_true",
        help="Only include wishlist games, not 'want to play'",
    )
    parser.add_argument(
        "--want-to-play-only",
        action="store_true",
        help="Only include 'want to play' games, not wishlist",
    )
    parser.add_argument(
        "--show-checked-out",
        action="store_true",
        help="Include games that are currently checked out",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (optional, defaults to stdout)",
        default=None,
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        print("\nTo export your BGG collection:")
        print("1. Go to https://boardgamegeek.com/collection/user/YOUR_USERNAME")
        print("2. Click the download icon (arrow pointing down)")
        print("3. Save as bgg_games.csv in this directory")
        return

    include_wishlist = not args.want_to_play_only
    include_want_to_play = not args.wishlist_only

    # Fetch both data sources
    library_games = fetch_tabletop_events_library()
    bgg_games = load_bgg_csv(
        csv_path,
        include_wishlist=include_wishlist,
        include_want_to_play=include_want_to_play,
    )

    if not bgg_games:
        print("No games found in your CSV. Check the file format.")
        return

    # Find matches
    matching = find_matching_games(library_games, bgg_games)

    if not args.show_checked_out:
        available = [g for g in matching if not g.is_checked_out]
        checked_out_count = len(matching) - len(available)
    else:
        available = matching
        checked_out_count = 0

    # Output results
    output_lines = []
    output_lines.append(f"Found {len(matching)} matching games!")
    if checked_out_count > 0:
        output_lines.append(f"({checked_out_count} currently checked out, use --show-checked-out to include)")
    output_lines.append("")
    output_lines.append("Games available in the Gen Con Games Library:")
    output_lines.append("-" * 50)

    for game in available:
        status = " [CHECKED OUT]" if game.is_checked_out else ""
        catalog = f" (#{game.library_catalog_number})" if game.library_catalog_number else ""
        # Build priority label (wishlist takes precedence over want-to-play)
        if game.wishlist_priority:
            priority_label = f"[Wishlist {game.wishlist_priority}]"
        elif game.want_to_play:
            priority_label = "[Want to Play]"
        else:
            priority_label = ""
        priority_prefix = f"{priority_label} " if priority_label else ""
        output_lines.append(f"- {priority_prefix}{game.name}{catalog}{status}")

    output_text = "\n".join(output_lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_text)
        print(f"Results written to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
