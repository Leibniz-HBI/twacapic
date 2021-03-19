# twacapic

Twitter Academic API Client

In development. Expect breaking changes and destructive bugs when updating to the latest version.


## Installation

Install via pip:

`pip install twacapic`


## Usage

```txt
usage: twacapic [-h] [-u USERLIST] [-g GROUPNAME] [-c GROUP_CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  -u USERLIST, --userlist USERLIST
                        path to list of user IDs, one per line. Required for first run only. Can be
                        used to add users to a group
  -g GROUPNAME, --groupname GROUPNAME
                        name of the group to collect. Results will be saved in folder
                        `results/GROUPNAME/`. Can be used to poll for new tweets of a group. Default:
                        "users"
  -c GROUP_CONFIG, --group_config GROUP_CONFIG
                        path to a custom group config file to define tweet data to be retrieved, e.g.
                        retweets, mentioned users, attachments. A template named `group_config.yaml`
                        can be found in any already created group folder.
```

At the moment twacapic can only collect the latest 100 tweets of a list of users and then poll for new tweets afterwards if called again with the same group name.

### Authorisation with the Twitter API

At first use, it will prompt you for your API credentials, which you find [here](https://developer.twitter.com/en/portal/projects-and-apps). These credentials will be stored in a file in the working directory, so make sure that the directory is readable by you and authorised users only.

For non-interactive use, e.g. when automatically deploying twacapic to a server, this file can be used as a template and should always be placed in the working directory of twacapic.

### Example

`twacapic -g USER_GROUP_NAME -u PATH_TO_USER_CSV`

`USER_GROUP_NAME` should be the name of the results folder that is meant to be created and will contain raw json responses from Twitter.

`PATH_TO_USER_CSV` should be a path to a list of Twitter user IDs, without header, one line per user ID.

Afterwards you can poll for new tweets of a user group by running simply:

`twacapic -g USER_GROUP_NAME`

Enjoy!


### Config Template

The group config is a yaml file in the following form:

```yaml
fields:
  attachments: No
  author_id: No
  context_annotations: No
  conversation_id: No
  created_at: No
  entities: No
  geo: No
  in_reply_to_user_id: No
  lang: No
  non_public_metrics: No
  organic_metrics: No
  possibly_sensitive: No
  promoted_metrics: No
  public_metrics: No
  referenced_tweets: No
  reply_settings: No
  source: No
  withheld: No
expansions:
  author_id: No
  referenced_tweets.id: No
  in_reply_to_user_id: No
  attachments.media_keys: No
  attachments.poll_ids: No
  geo.place_id: No
  entities.mentions.username: No
  referenced_tweets.id.author_id: No
```

An explanation of the fields and expansions can be found in Twitter's API docs:

  - [Fields](https://developer.twitter.com/en/docs/twitter-api/fields)
  - [Expansions](https://developer.twitter.com/en/docs/twitter-api/expansions)


## Dev Install

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Clone repository
3. In the directory run `poetry install`
4. Run `poetry shell` to start development virtualenv
5. Run `twacapic` to enter API keys. Ignore the IndexError.
6. Run `pytest` to run all tests
