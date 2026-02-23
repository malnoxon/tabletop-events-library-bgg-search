# Gen Con Games Library BGG Wishlist Matcher

Find games that are both in your BoardGameGeek wishlist/marked as want-to-play and part of the a specific tabletop.events games library https://tabletop.events/libraries/gen-con-games-library-the

## Exporting Your BGG Collection

1. Go to your BGG collection: `https://boardgamegeek.com/collection/user/YOUR_USERNAME`
2. Download all as CSV
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
