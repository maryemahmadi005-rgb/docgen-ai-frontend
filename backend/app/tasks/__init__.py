"""
Enregistrement de la tâche périodique auprès de Celery beat.
Fichier séparé de polling_task.py pour garder ce dernier testable sans Celery.
"""

from celery import shared_task
from app.tasks.polling_task import PollingTask


@shared_task(name="tasks.run_polling")
def run_polling_task():
    from app.container import get_polling_task  # factory d'injection de dépendances
    task = get_polling_task()
    return task.run()

# celeryconfig.py (extrait) :
# CELERYBEAT_SCHEDULE = {
#     "poll-github-repositories": {
#         "task": "tasks.run_polling",
#         "schedule": 300.0,  # toutes les 5 minutes
#     },
# }