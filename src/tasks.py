'''The module with celery tasks'''
import celery
from celery.utils.log import get_task_logger
from notification import Notification
import settings
from src import notification

app = celery.Celery('github-notification')

app.conf.update(broker_url=settings.CELERY_BROKER_URL,
                result_backend=settings.CELERY_RESULT_BACKEND)


app.conf.beat_schedule = {
    'add-every-2-seconds': {
        'task': 'tasks.handle_urls',
        'schedule': 2.0,
    },
}

logger = get_task_logger(__name__)

@app.task
def handle_url(url):
    '''Handle the specific url'''
    logger.info('Handle %s is started.', url)
    notification = Notification()
    notification.get_repo_stars_diff(url)
    logger.info('Handle %s is finished.', url)

@app.task
def handle_repo(repo_id):
    '''Handle repo by id'''
    logger.info('Handle %s is started.', repo_id)
    notification = Notification()


    logger.info('Handle %s is finished.', repo_id)


@app.task
def handle_urls():
    '''Handle all urls from the DB'''
    notification = Notification()
    for repo in notification.get_repos():
        handle_url.delay(repo)
    logger.info('Handle urls is started.')


app.conf.timezone = 'UTC'
