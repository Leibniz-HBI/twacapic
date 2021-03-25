import json
import os
import shutil
import time
from glob import glob
from pathlib import Path

import twacapic.templates
import yaml
from loguru import logger
from twacapic.auth import get_api
from TwitterAPI.TwitterError import TwitterConnectionError, TwitterRequestError

logger.remove()


class UserGroup:

    def __init__(self, path=None, name=None, config=None):

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
            self.user_ids = [
                item for item in os.listdir(self.path) if os.path.isdir(
                    os.path.join(self.path, item)
                    )
            ]

        if config is not None:
            shutil.copy(config, f'{self.path}/group_config.yaml')
        elif not os.path.isfile(f'{self.path}/group_config.yaml'):
            with open(f'{self.path}/group_config.yaml', 'w') as f:
                yaml.dump(twacapic.templates.group_config, f)

    @property
    def config(self):
        with open(f'{self.path}/group_config.yaml', 'r') as f:
            config = yaml.safe_load(f)

            return config

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

    def request_tweets(self, api, user_id, params, get_all_pages=False):

        @retry
        def get_page(params):

            response = api.request(f'users/:{user_id}/tweets', params)

            try:
                assert response.status_code == 200
                logger.debug(response.text)
            except AssertionError as e:
                logger.warning(response.text)
                raise e

            tweets = json.loads(response.text)

            if 'errors' in tweets and 'data' not in tweets:

                logger.error(tweets["errors"])

                if tweets['errors'][0]['title'] == 'Not Found Error':
                    shutil.copytree(Path.cwd()/'results'/self.name/user_id,
                                    Path.cwd()/'results'/f'deleted_{self.name}'/user_id,
                                    dirs_exist_ok=True
                                    )
                    shutil.rmtree(Path.cwd()/'results'/self.name/user_id)
                elif tweets['errors'][0]['title'] == 'Forbidden':
                    shutil.copytree(Path.cwd()/'results'/self.name/user_id,
                                    Path.cwd()/'results'/f'suspended_{self.name}'/user_id,
                                    dirs_exist_ok=True
                                    )
                    shutil.rmtree(Path.cwd()/'results'/self.name/user_id)
                elif tweets['errors'][0]['title'] == 'Authorization Error':
                    shutil.copytree(Path.cwd()/'results'/self.name/user_id,
                                    Path.cwd()/'results'/f'protected_{self.name}'/user_id,
                                    dirs_exist_ok=True
                                    )
                    shutil.rmtree(Path.cwd()/'results'/self.name/user_id)
                else:
                    raise TwitterRequestError(200, f"{tweets['errors']}")

                self.user_ids.remove(user_id)

                return None

            if 'errors' in tweets and 'data' in tweets:

                for error in tweets['errors']:
                    logger.warning(error)

            result_count = tweets['meta']['result_count']

            if result_count == 0:
                logger.info(f'No new tweets found for {user_id}.')
                return None
            else:
                logger.info(f'{result_count} tweets found for {user_id}')

            oldest_id = tweets['meta']['oldest_id']
            newest_id = tweets['meta']['newest_id']

            with open(f'results/{self.name}/{user_id}/{newest_id}_{oldest_id}.json', 'w',
                      encoding='utf8') as f:
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

        field_config = self.config['fields']

        fields = [
            field for field in field_config if field_config[field]
        ]

        expansions_config = self.config['expansions']

        expansions = [
            expansion for expansion in expansions_config if expansions_config[expansion]
        ]

        iterlist = self.user_ids.copy()
        # copy needed because self.user_ids changes during iteration … what a bedbug …

        for user_id in iterlist:

            params = {}
            params['tweet.fields'] = ','.join(fields)
            params['expansions'] = ','.join(expansions)

            logger.info(f"Collecting tweets for user {user_id} …")

            meta_file_path = f'{self.path}/{user_id}/meta.yaml'

            if not os.path.isfile(meta_file_path):

                params['max_results'] = max_results_per_call
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

                params['max_results'] = max_results_per_call

                try:
                    params['since_id'] = user_metadata['newest_id']
                except KeyError:
                    pass

                collected_ids = self.request_tweets(api, user_id, params, get_all_pages=True)

                if collected_ids is not None:
                    oldest_id, newest_id = collected_ids

                    user_metadata['newest_id'] = newest_id

                    with open(meta_file_path, 'w') as metafile:
                        yaml.dump(user_metadata, metafile)


def retry(func):

    def retried_func(*args, **kwargs):
        max_tries = 10
        tries = 0
        total_sleep_seconds = 0

        while True:
            try:
                resp = func(*args, **kwargs)

            except (TwitterConnectionError, TwitterRequestError, AssertionError) as e:

                logger.warning(e)

                if tries < max_tries:

                    tries += 1

                    sleep_seconds = min(((tries * 2) ** 2), max(900 - total_sleep_seconds, 30))
                    total_sleep_seconds = total_sleep_seconds + sleep_seconds
                else:
                    logger.exception('Maximum retries reached. Raising Exception …')
                    raise e

                logger.warning(f"Retry in {sleep_seconds} seconds …")
                time.sleep(sleep_seconds)
                continue

            break

        return resp

    return retried_func
