'''The module with celery tasks'''
import celery
from celery.utils.log import get_task_logger
from notification import Notification
import settings
from models import Repo, session_factory

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
    notification.update_repo_stars(url)
    logger.info('Handle %s is finished.', url)

@app.task
def handle_repo(repo_id: int):
    '''Handle repo by id'''
    logger.info('Handle %s is started.', repo_id)
    notification = Notification()
    diff_result = notification.update_repo_stars(repo_id)
    
    
    logger.info('Handle %s is finished.', repo_id)


@app.task
def handle_urls():
    '''Handle all urls from the DB'''

    repos = []
    with session_factory() as session:
        repos = session.filter(Repo).all()


    notification = Notification()
    for repo in repos:
        handle_repo.delay(repo.id)
    logger.info('Handle urls is started.')


app.conf.timezone = 'UTC'
