from django.core.management.base import BaseCommand

from django_simple_tasks._private.utils import logger
from django_simple_tasks.models import TaskModel, Status


class Command(BaseCommand):
    help = "Marks failed tasks as ready to consume"

    def handle(self, *args, **options):
        TaskModel.objects.filter(status=Status.FAILED).update(status=Status.CREATED, restart_attempts=0)
        logger.info("Done")
