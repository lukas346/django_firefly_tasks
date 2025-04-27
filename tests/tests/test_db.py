from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from django_firefly_tasks._private.utils import get_latest_task
from django_firefly_tasks.models import Status, TaskModel


class DatabaseTest(TestCase):
    def test_get_task_simple_0(self):
        time_offset = 0
        queue = "default"

        for _ in range(4):
            time_offset += 10

            TaskModel.objects.create(
                func_name="test",
                queue=queue,
                status=Status.CREATED,
                max_retries=0,
                not_before=timezone.now() + timedelta(seconds=time_offset),
            )

        TaskModel.objects.create(func_name="test", queue=queue, status=Status.CREATED, max_retries=0, not_before=None)

        task = get_latest_task(queue)
        self.assertEqual(task.id, 5)
        self.assertIsNone(task.not_before)
        task.set_as_completed()
        task.save()

        for i in range(1, 5):
            task = get_latest_task(queue)
            self.assertEqual(task.id, i)
            self.assertIsNotNone(task.not_before)
            task.set_as_completed()
            task.save()

    def test_get_task_simple_1(self):
        queue = "default"

        TaskModel.objects.create(
            func_name="test", queue=queue, status=Status.CREATED, max_retries=0, not_before=timezone.now()
        )

        for _ in range(4):
            TaskModel.objects.create(
                func_name="test", queue=queue, status=Status.CREATED, max_retries=0, not_before=None
            )

        for i in range(2, 6):
            task = get_latest_task(queue)
            self.assertEqual(task.id, i)
            self.assertIsNone(task.not_before)
            task.set_as_completed()
            task.save()

        task = get_latest_task(queue)
        self.assertEqual(task.id, 1)
        self.assertIsNotNone(task.not_before)
        task.set_as_completed()
        task.save()
