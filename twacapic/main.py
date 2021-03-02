import os

from searchtweets import ResultStream, gen_request_parameters, load_credentials
from twacapic.auth import save_credentials


def run():
    print("Hello friend …")

    if not os.path.isfile('twitter_keys.yaml'):
        print("Please enter your API key:")
        consumer_key = input()
        print("Please enter your API secret:")
        consumer_secret = input()
        print("Please enter your bearer_token:")
        consumer_secret = input()

        save_credentials('twitter_keys.yaml', consumer_key, consumer_secret)

    search_args = load_credentials('twitter_keys.yaml',
                                   yaml_key='search_tweets_v2',
                                   env_overwrite=False)

    query = gen_request_parameters(query='from:36476777', since_id=1363967624963633151, results_per_call=500)

    print(query)

    result_stream = ResultStream(request_parameters=query, max_results=500, max_requests=1, **search_args)

    print(result_stream)

    tweets = list(result_stream.stream())

    print(tweets)

    print(len(tweets))


if __name__ == '__main__':
    run()
