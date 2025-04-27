from django.core.management.base import BaseCommand

from django_firefly_tasks._private.utils import logger
from django_firefly_tasks.models import Status, TaskModel


class Command(BaseCommand):
    help = "Deletes completed tasks."

    def handle(self, *args, **options):
        ids = list(TaskModel.objects.filter(status=Status.COMPLETED).values_list("pk"))
        TaskModel.objects.filter(status=Status.COMPLETED).delete()

        logger.info(f"Deleted completed tasks: {ids}")
