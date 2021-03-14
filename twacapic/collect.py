import json
import os
import time
from glob import glob

import yaml
from twacapic.auth import get_api
from TwitterAPI.TwitterError import TwitterConnectionError, TwitterRequestError


class UserGroup:

    def __init__(self, path=None, name=None):

        self.source_path = path
        self.path = f'results/{name}'
        self.name = name

        if path is not None:
            self.user_ids = []
            with open(path, 'r') as file:
                for line in file:
                    user_id = line.strip()
                    os.makedirs(f'results/{name}/{user_id}', exist_ok=True)
                    self.user_ids.append(user_id)
        else:
            self.user_ids = os.listdir(self.path)

    def request_tweets(self, api, user_id, params, get_all_pages=False):

        @retry
        def get_page(params):

            response = api.request(f'users/:{user_id}/tweets', params)

            assert response.status_code == 200

            tweets = json.loads(response.text)

            if tweets['meta']['result_count'] == 0:
                return None

            oldest_id = tweets['meta']['oldest_id']
            newest_id = tweets['meta']['newest_id']

            with open(f'results/{self.name}/{user_id}/{newest_id}_{oldest_id}.json', 'w', encoding='utf8') as f:
                json.dump(tweets, f, ensure_ascii=False)

            return oldest_id, newest_id, tweets

        try:
            oldest_id, newest_id, tweets = get_page(params)
        except TypeError:
            return None

        if get_all_pages is True:
            while 'next_token' in tweets['meta']:

                params['pagination_token'] = tweets['meta']['next_token']

                oldest_id, new_newest_id, tweets = get_page(params)

        return oldest_id, newest_id

    def collect(self, credential_path='twitter_keys.yaml', max_results_per_call=100):

        api = get_api(credential_path)

        for user_id in self.user_ids:
            print(f"Collecting tweets for user {user_id} …")

            meta_file_path = f'results/{self.name}/{user_id}/meta.yaml'

            if not os.path.isfile(meta_file_path):

                params = {'max_results': max_results_per_call}
                collected_ids = self.request_tweets(api, user_id, params)

                user_metadata = {}

                if collected_ids is not None:
                    oldest_id, newest_id = collected_ids
                    user_metadata['newest_id'] = newest_id
                    user_metadata['oldest_id'] = oldest_id

                with open(meta_file_path, 'w') as metafile:
                    yaml.dump(user_metadata, metafile)

            else:

                with open(meta_file_path, 'r') as metafile:
                    user_metadata = yaml.safe_load(metafile)

                params = {'max_results': max_results_per_call,
                          'since_id': user_metadata['newest_id']}

                collected_ids = self.request_tweets(api, user_id, params, get_all_pages=True)

                if collected_ids is not None:
                    oldest_id, newest_id = collected_ids

                    user_metadata['newest_id'] = newest_id

                    with open(meta_file_path, 'w') as metafile:
                        yaml.dump(user_metadata, metafile)

    @property
    def tweet_files(self):
        files = {}
        for user_id in self.user_ids:
            files[user_id] = glob(f'{self.path}/{user_id}/*.json')
        return files

    @property
    def meta(self):
        meta = {}
        for user_id in self.user_ids:
            with open(f'{self.path}/{user_id}/meta.yaml', 'r') as f:
                meta[user_id] = yaml.safe_load(f)
        return meta


def retry(func):

    def retried_func(*args, **kwargs):
        max_tries = 10
        tries = 0
        total_sleep_seconds = 0

        while True:
            try:
                resp = func(*args, **kwargs)

            except (TwitterConnectionError, TwitterRequestError, AssertionError) as e:

                print(e)

                if tries < max_tries:

                    tries += 1

                    sleep_seconds = min(((tries * 2) ** 2), max(900 - total_sleep_seconds, 30))
                    total_sleep_seconds = total_sleep_seconds + sleep_seconds
                else:
                    print('Maximum retries reached. Raising Exception …')
                    raise e

                print(f"Retry in {sleep_seconds} seconds …")
                time.sleep(sleep_seconds)
                continue

            break

        return resp

    return retried_func
