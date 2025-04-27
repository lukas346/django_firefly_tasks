from django.core.management.base import BaseCommand

from django_firefly_tasks._private.utils import logger
from django_firefly_tasks.models import Status, TaskModel


class Command(BaseCommand):
    help = "Deletes failed tasks."

    def handle(self, *args, **options):
        ids = list(TaskModel.objects.filter(status=Status.FAILED).values_list("pk"))
        TaskModel.objects.filter(status=Status.FAILED).delete()

        logger.info(f"Deleted failed tasks: {ids}")
