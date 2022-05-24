from datetime import datetime
from functools import reduce
import unittest
from notification import Notification, SubscribeResult, UnsubscribeResut
from models import Repo, User, session_factory, engine


class NotificationTestCase(unittest.TestCase):
    def tearDown(self):
        '''Setup'''

        with engine.connect() as con:
            con.execute('DELETE FROM user_repo_association',)

        with session_factory() as session:
            session.query(Repo).delete()
            session.query(User).delete()

            session.commit()


    def test_subscribe_repo(self):
        '''Test subscribe'''

        # Arrange
        notification = Notification()
        url = 'https://github.com/alexpantyukhin/aiohttp-session-mongo'
        teleg_user_id = 1

        # Act
        result = notification.subscribe(teleg_user_id, url)

        # Assert
        assert result == SubscribeResult.OK

        with session_factory() as session:
            repo = session.query(Repo).filter_by(url = url).first()
            assert repo is not None

            users = repo.users
            assert len(users) == 1

            assert users[0].teleg_user_id == teleg_user_id

    def test_subscribe_more_then_once(self):
        '''Test subscribe'''

        # Arrange
        notification = Notification()
        url = 'https://github.com/alexpantyukhin/aiohttp-session-mongo'
        teleg_user_id = 1

        # Act
        result = notification.subscribe(teleg_user_id, url)
        assert result == SubscribeResult.OK

        result = notification.subscribe(teleg_user_id, url)

        # Assert
        assert result == SubscribeResult.ALREADY_SUBSCRIBE


    def test_unsibscribe_repo(self):
        '''Test unsubscribe'''

        # Arrange
        notification = Notification()
        url = 'https://github.com/alexpantyukhin/aiohttp-session-mongo'
        teleg_user_id = 1

        # Act
        result = notification.subscribe(teleg_user_id, url)
        assert result == SubscribeResult.OK

        result = notification.unsubscribe(teleg_user_id, url)

        # Assert
        assert result == UnsubscribeResut.OK
        with session_factory() as session:
            repo = session.query(Repo).filter_by(url = url).first()
            assert repo is not None

            users = repo.users
            assert len(users) == 0

    def test_unsibscribe_more_then_once_repo(self):
        '''Test unsubscribe'''

        # Arrange
        notification = Notification()
        url = 'https://github.com/alexpantyukhin/aiohttp-session-mongo'
        teleg_user_id = 1

        # Act
        result = notification.subscribe(teleg_user_id, url)
        assert result == SubscribeResult.OK

        result = notification.unsubscribe(teleg_user_id, url)
        assert result == UnsubscribeResut.OK

        result = notification.unsubscribe(teleg_user_id, url)

        # Assert
        assert result == UnsubscribeResut.REPO_MISSING

    def test_get_user_repos(self):
        '''Test user repos'''

        # Arrange
        notification = Notification()
        url_1 = 'https://github.com/alexpantyukhin/aiohttp-session-mongo'
        url_2 = 'https://github.com/stretchr/testify'
        teleg_user_id = 1

        # Act
        result = notification.subscribe(teleg_user_id, url_1)
        assert result == SubscribeResult.OK

        result = notification.subscribe(teleg_user_id, url_2)
        assert result == SubscribeResult.OK

        result = notification.get_user_repos(teleg_user_id)

        # Assert
        assert set(result) == set([url_1, url_2])


    def test_update_repo_stars(self):
        '''Test Update repo stars'''

        # Arrange
        stars_pages = [
            [
                {
                    'login': 'login1',
                    'starred_at': datetime.fromisoformat('2022-01-01T00:00:00.000+00:00')
                },
                {
                    'login': 'login2',
                    'starred_at': datetime.fromisoformat('2022-01-02T00:00:00.000+00:00')
                }
            ],
            [
                {
                    'login': 'login3',
                    'starred_at': datetime.fromisoformat('2022-01-03T00:00:00.000+00:00')
                },
                {
                    'login': 'login4',
                    'starred_at': datetime.fromisoformat('2022-01-04T00:00:00.000+00:00')
                }
            ],
            [
                {
                    'login': 'login5',
                    'starred_at': datetime.fromisoformat('2022-01-05T00:00:00.000+00:00')
                }
            ],
        ]

        count = len(reduce(list.__add__, stars_pages))

        notification = Notification(get_repo_stars_count=lambda _: count,
                                    get_repo_stargazers_page=lambda repo_url, page, size: stars_pages[page-1],
                                    page_size=len(stars_pages[0]))

        # Act
        url = 'https://github.com/alexpantyukhin/aiohttp-session-mongo'
        notification.subscribe(1, url)

        repo = None
        with session_factory() as session:
            repo = session.query(Repo).filter_by(url=url).first()

        result = notification.update_repo_stars(repo.id)

        # Assert
        with session_factory() as session:
            repo = session.query(Repo).filter_by(url=url).first()
            assert repo.last_updated_time is not None

        assert result.initiated is False
        assert set(result.teleg_subscribed_users) == set([1])
        assert len(result.added_stars) == 0
        assert len(result.removed_stars) == 0


    def test_update_repo_stars_when_stars_changed(self):
        '''Test Update repo stars when stars changed'''

        # Arrange
        stars_pages = [
            [
                {
                    'login': 'login1',
                    'starred_at': datetime.fromisoformat('2022-01-01T00:00:00.000+00:00')
                },
                {
                    'login': 'login2',
                    'starred_at': datetime.fromisoformat('2022-01-02T00:00:00.000+00:00')
                }
            ],
            [
                {
                    'login': 'login3',
                    'starred_at': datetime.fromisoformat('2022-01-03T00:00:00.000+00:00')
                },
                {
                    'login': 'login4',
                    'starred_at': datetime.fromisoformat('2022-01-04T00:00:00.000+00:00')
                }
            ],
            [
                {
                    'login': 'login5',
                    'starred_at': datetime.fromisoformat('2022-01-05T00:00:00.000+00:00')
                }
            ],
        ]

        count = len(reduce(list.__add__, stars_pages))

        notification = Notification(get_repo_stars_count=lambda _: count,
                                    get_repo_stargazers_page=lambda repo_url, page, size: stars_pages[page-1],
                                    page_size=len(stars_pages[0]))

        # Act
        url = 'https://github.com/alexpantyukhin/aiohttp-session-mongo'
        notification.subscribe(1, url)

        repo_id = None
        with session_factory() as session:
            repo_id = session.query(Repo).filter_by(url=url).first().id

        result = notification.update_repo_stars(repo_id)

        with session_factory() as session:
            repo = session.query(Repo).filter_by(url=url).first()
            repo_id = repo.id
            repo.last_updated_time = datetime.fromisoformat('2022-01-01T00:00:00.000+00:00')
            session.commit()

        stars_pages[-1][0] = {
                'login': 'login10',
                'starred_at': datetime.fromisoformat('2022-01-10T00:00:00.000+00:00')
            }

        result = notification.update_repo_stars(repo_id)

        # Assert
        assert result.initiated is True
        assert set(result.teleg_subscribed_users) == set([1])

        assert len(result.added_stars) == 1
        assert result.added_stars[0] == 'login10'
        assert len(result.removed_stars) == 1
        assert result.removed_stars[0] == 'login5'
