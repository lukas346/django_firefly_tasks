from django.core.management.base import BaseCommand

from django_firefly_tasks._private.consts import DEFAULT_QUEUE
from django_firefly_tasks._private.consumers import task_consumer


class Command(BaseCommand):
    help = "Consumes scheduled tasks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--queue",
            type=str,
            help="Queue to consume from. Default queue if left empty.",
        )

    def handle(self, *args, **options):
        queue = options["queue"] or DEFAULT_QUEUE

        try:
            task_consumer(queue)
        except KeyboardInterrupt:
            pass
