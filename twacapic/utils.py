from datetime import datetime


def get_date_from_tweet_id(tweet_id):

    shifted = int(tweet_id) >> 22
    timestamp = shifted + 1288834974657
    time_created = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d')

    return {'timestamp': timestamp, 'date': time_created}
