from datetime import datetime
from typing import Dict, List
import json
import aiohttp
import settings

async def _get_request_content(base_url, page=None, size=None, headers=None):
    url = base_url
    params = []
    if page is not None:
        params.append(f'page={str(page)}')

    if size is not None:
        params.append(f'per_page={str(size)}')

    params_str = '&'.join(params)
    if len(params) > 0:
        url += '?' + params_str

    if settings.GITHUB_KEY is not None:
        if headers is None:
            headers = {}

        headers['Authorization'] = f'token {settings.GITHUB_KEY}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            content = await response.text()
            return json.loads(content)

async def get_repo_stars_count(repo_url: str) -> int:
    '''Get repos count async'''
    content = await _get_request_content(repo_url)
    return content['stargazers_count']


def __parse_star_item(content: Dict[str, str]) -> Dict[str, str]:
    return {
        'login': content['user']['login'],
        'starred_at': datetime.strptime(content['starred_at'], '%Y-%m-%dT%H:%M:%S%z').isoformat()
    }

async def get_repo_stargazers_page(repo_url: str, page: int, size:int) -> List[Dict[str, str]]:
    '''Get repos stars page'''
    content = await _get_request_content(repo_url,
                                   page=page,
                                   size=size,
                                   headers={'Accept':'application/vnd.github.v3.star+json'})

    return list(map(__parse_star_item, content))
