import json
import os

from twacapic.auth import get_api


class UserGroup:

    def __init__(self, path, name):

        self.path = path
        self.name = name
        self.user_ids = []

        with open(path, 'r') as file:
            for line in file:
                user_id = line.strip()
                os.makedirs(f'results/{name}/{user_id}', exist_ok=True)
                self.user_ids.append(user_id)

    def collect(self, credential_path='twitter_keys.yaml'):

        api = get_api(credential_path)

        for user_id in self.user_ids:

            params = {'max_results': 100}
            response = api.request(f'users/:{user_id}/tweets', params)

            assert response.status_code == 200

            tweets = json.loads(response.text)
            oldest_id = tweets['meta']['oldest_id']
            newest_id = tweets['meta']['newest_id']

            with open(f'results/{self.name}/{user_id}/{newest_id}_{oldest_id}.json', 'w', encoding='utf8') as f:
                json.dump(tweets, f, ensure_ascii=False)
