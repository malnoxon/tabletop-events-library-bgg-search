# Gen Con Games Library BGG Wishlist Matcher

Find games that are both in your BoardGameGeek collection AND available in the [Gen Con Games Library](https://tabletop.events/libraries/gen-con-games-library-the).

## Installation

```bash
pip install -r requirements.txt
```

## Exporting Your BGG Collection

1. Go to your BGG collection: `https://boardgamegeek.com/collection/user/YOUR_USERNAME`
2. Click the download icon (arrow pointing down) to export as CSV
3. Save the file as `bgg_games.csv` in this directory

## Usage

```bash
# Basic usage - finds wishlist and want-to-play games
python find_library_wishlist_games.py

# Specify a different CSV file
python find_library_wishlist_games.py --csv my_collection.csv

# Only check wishlist games
python find_library_wishlist_games.py --wishlist-only

# Only check want-to-play games
python find_library_wishlist_games.py --want-to-play-only

# Include currently checked-out games in results
python find_library_wishlist_games.py --show-checked-out

# Save to file
python find_library_wishlist_games.py -o matches.txt
```

## How It Works

1. Loads your BGG CSV export and filters to wishlist/want-to-play games
2. Fetches all games from the Gen Con Games Library API (~2,000+ games)
3. Matches games by BGG ID
4. Outputs matching games sorted alphabetically, with catalog numbers
