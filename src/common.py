from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse

@dataclass
class ApiUrlsRepoResult:
    api_repo_url: str
    api_repo_stars_url: str


def get_message_lines(lines: List[str]) -> str:
    '''Join string list to string'''
    return '\n'.join(lines)


def get_api_repo_url_from_repo_url(repo_url: str) -> ApiUrlsRepoResult:
    '''Get stars api repo url basing on the github api repo'''
    parsed_url = urlparse(repo_url)

    api_repo_url = f'https://api.github.com/repos{parsed_url.path}'
    api_repo_stars_url = f'https://api.github.com/repos{parsed_url.path}/stargazers'

    return ApiUrlsRepoResult(api_repo_url=api_repo_url, api_repo_stars_url=api_repo_stars_url)


def generate_notification_message(repo_url: str,
                                  added_stars_subscribers: List[str],
                                  removed_stars_subscribers: List[str]) -> str:
    '''Generates the notification message'''

    message_lines = [f'Repo: {repo_url}', '']

    if len(added_stars_subscribers) > 0:
        new_subscribers = ','.join(added_stars_subscribers)
        message_lines.append(f'New subscribers: {new_subscribers}')

    if len(removed_stars_subscribers) > 0:
        removed_subscribers = ','.join(removed_stars_subscribers)
        message_lines.append(f'Removed subscribers: {removed_subscribers}')

    message = get_message_lines(message_lines)
    return message
