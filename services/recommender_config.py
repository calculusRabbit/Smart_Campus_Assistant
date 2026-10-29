# settings for the event recommendations (services/event_recommender.py)

# events that started up to this many days ago still count, 0 means only events that are not over
# one year for now because the event data is old, go back to 0 when the events are fresh
LOOKBACK_DAYS = 365

# events that are more than this many days away are not shown
LOOKAHEAD_DAYS = 30

# how well an event has to match, the requirements say 30% for now
MIN_SCORE = 0.30

# how many matches to get from the index before we throw out the old ones
SEARCH_SIZE = 150

# events that are coming up soon get a boost to their score
SOON_DAYS = 3
SOON_BOOST = 0.1

# for now the text the student wrote is saved in the interests list (there is no text column yet)
# an item with more words than this is the text, a shorter one is a tag like "coding"
MAX_TAG_WORDS = 3
