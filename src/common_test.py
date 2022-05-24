from re import A
import unittest
from common import get_api_repo_url_from_repo_url

class NotificationTestCase(unittest.TestCase):
    def test_get_api_repo_url_from_repo_url(self):
        # Arrange
        url = 'https://github.com/alexpantyukhin/aiohttp-session-mongo'
        api_repo_url_expected = 'https://api.github.com/repos/alexpantyukhin/aiohttp-session-mongo'
        api_repo_stars_url_expected = 'https://api.github.com/repos/alexpantyukhin/aiohttp-session-mongo/stargazers'

        # Act
        api_urls_repo_result = get_api_repo_url_from_repo_url(url)

        # Assert:
        assert api_urls_repo_result.api_repo_url == api_repo_url_expected
        assert api_urls_repo_result.api_repo_stars_url == api_repo_stars_url_expected
