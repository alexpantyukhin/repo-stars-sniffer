from dataclasses import dataclass
from typing import List, Tuple
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
