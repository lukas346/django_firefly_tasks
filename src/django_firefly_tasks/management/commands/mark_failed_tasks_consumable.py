from django.core.management.base import BaseCommand

from django_firefly_tasks._private.utils import logger
from django_firefly_tasks.models import Status, TaskModel


class Command(BaseCommand):
    help = "Marks failed tasks as ready to consume"

    def handle(self, *args, **options):
        TaskModel.objects.filter(status=Status.FAILED).update(status=Status.CREATED, retry_attempts=0)
        logger.info("Done")
