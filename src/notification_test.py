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
            repo = session.query(Repo).filter_by(url = url).first()

        result = notification.update_repo_stars(repo.id)

        # Assert
        assert result.initiated is False
        assert set(result.teleg_subscribed_users) == set([1])


# def test_docker_run_redis_with_password():
#     config = RedisContainer()
#     with config as redis:
#         client = redis.get_client(decode_responses=True)

#         client.set("hello", "world")
#         print(client.get("hello"))
#         assert client.get("hello") == "world"


# def batch(items, page_size):
#     iterator = iter(items)

#     buffer = []
#     result = []
#     while True:
#         value = next(iterator, None)
#         if value is None:
#             break

#         buffer.append(value)
#         if len(buffer) == page_size:
#             result.append(buffer)
#             buffer = []

#     if len(buffer) > 0:
#         result.append(buffer)

#     return result


# def test_notification_get_repo_stars_diff():
#     config = RedisContainer()
#     with config as redis:
#         client = redis.get_client(decode_responses=True)
#         items = []
#         for i in range(1, 11):
#             items.append({
#                 'starred_at': datetime(2022, 1, i),
#                 'login': 'login' + str(i)
#             })

#         repo_name = 'https://api.github.com/repos/alexpantyukhin/go-pattern-match/stargazers'
#         serializaed_items = list(map(lambda x: notification.StarItem.from_dict(x).to_json() , items))
#         client.rpush(f'stars_{repo_name}', *serializaed_items)

#         githib_items = items.copy()
#         del githib_items[5]
#         githib_items.append({
#             'starred_at': datetime(2022, 1, 20),
#             'login': 'login' + str(20)
#         })
#         page_size = 3
#         github_paged_items = batch(githib_items, page_size)


#         n = notification.Notification(
#             client,
#             get_repo_stars_count=lambda _: len(githib_items),
#             get_repo_stargazers_page = lambda _, x: github_paged_items[x - 1],
#             page_size=page_size)

#         result = n.update_repo_stars(repo_name)

#         assert len(result[0]) == 1
#         assert len(result[1]) == 1


# test_notification_get_repo_stars_diff()
