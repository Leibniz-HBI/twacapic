import json
import os

import yaml
from twacapic.auth import get_api


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

    def request_tweets(self, api, user_id, params):
        response = api.request(f'users/:{user_id}/tweets', params)

        assert response.status_code == 200

        tweets = json.loads(response.text)
        oldest_id = tweets['meta']['oldest_id']
        newest_id = tweets['meta']['newest_id']

        with open(f'results/{self.name}/{user_id}/{newest_id}_{oldest_id}.json', 'w', encoding='utf8') as f:
            json.dump(tweets, f, ensure_ascii=False)

        return oldest_id, newest_id

    def collect(self, credential_path='twitter_keys.yaml'):

        api = get_api(credential_path)

        for user_id in self.user_ids:

            meta_file_path = f'results/{self.name}/{user_id}/meta.yaml'

            if not os.path.isfile(meta_file_path):

                params = {'max_results': 100}
                oldest_id, newest_id = self.request_tweets(api, user_id, params)

                user_metadata = {}
                user_metadata['newest_id'] = newest_id
                user_metadata['oldest_id'] = oldest_id

                with open(meta_file_path, 'w') as metafile:
                    yaml.dump(user_metadata, metafile)

            else:

                with open(meta_file_path, 'r') as metafile:
                    user_metadata = yaml.safe_load(metafile)

                params = {'max_results': 100, 'since_id': user_metadata['newest_id']}
                oldest_id, newest_id = self.request_tweets(api, user_id, params)

                user_metadata['newest_id'] = newest_id

                with open(meta_file_path, 'w') as metafile:
                    yaml.dump(user_metadata, metafile)

