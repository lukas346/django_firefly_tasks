from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from django_firefly_tasks.models import Status, TaskModel


class CommandTestCase(TestCase):
    def test_command_delete_failed_tasks(self):
        for _ in range(5):
            TaskModel.objects.create(
                func_name="app.tasks.test", queue="default", status=Status.FAILED, failed=timezone.now(), max_retries=0
            )

        TaskModel.objects.create(
            func_name="app.tasks.test", queue="default", status=Status.COMPLETED, failed=timezone.now(), max_retries=0
        )

        self.assertEqual(TaskModel.objects.filter(status=Status.FAILED).count(), 5)

        call_command(
            "delete_failed_tasks",
        )

        self.assertEqual(TaskModel.objects.filter(status=Status.FAILED).count(), 0)
        self.assertEqual(TaskModel.objects.filter(status=Status.COMPLETED).count(), 1)

    def test_command_delete_completed_tasks(self):
        for _ in range(5):
            TaskModel.objects.create(
                func_name="app.tasks.test",
                queue="default",
                status=Status.COMPLETED,
                failed=timezone.now(),
                max_retries=0,
            )

        TaskModel.objects.create(
            func_name="app.tasks.test", queue="default", status=Status.FAILED, failed=timezone.now(), max_retries=0
        )

        self.assertEqual(TaskModel.objects.filter(status=Status.COMPLETED).count(), 5)

        call_command(
            "delete_completed_tasks",
        )

        self.assertEqual(TaskModel.objects.filter(status=Status.COMPLETED).count(), 0)
        self.assertEqual(TaskModel.objects.filter(status=Status.FAILED).count(), 1)

    def test_command_mark_failed_tasks_consumable(self):
        for _ in range(5):
            TaskModel.objects.create(
                func_name="app.tasks.test", queue="default", status=Status.FAILED, failed=timezone.now(), max_retries=0
            )

        TaskModel.objects.create(
            func_name="app.tasks.test", queue="default", status=Status.CREATED, failed=timezone.now(), max_retries=0
        )

        self.assertEqual(TaskModel.objects.filter(status=Status.CREATED).count(), 1)

        call_command(
            "mark_failed_tasks_consumable",
        )

        self.assertEqual(TaskModel.objects.filter(status=Status.CREATED).count(), 6)
        self.assertEqual(TaskModel.objects.filter(status=Status.FAILED).count(), 0)
