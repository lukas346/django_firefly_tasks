from django.conf import settings
from django.test import TestCase
from django.db import transaction

from django_simple_tasks.models import TaskModel, Status
from django_simple_tasks._private.processors import task_processor

from tests.models import FooModel
from tests.tasks import add, async_add, create_foo, async_create_foo, failling, async_failling, restarting_failling, async_restarting_failling


class TasksTest(TestCase):
    def test_task_simple(self):
        task = add.schedule(1, 3)
    
        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        with transaction.atomic():
            task_processor(task)
        
        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        self.assertEqual(task.returned, 4)

    def test_model_task_simple(self):
        name = "FooBar"

        task = create_foo.schedule(name)
    
        self.assertEqual(task.func_name, "tests.tasks.create_foo")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        with transaction.atomic():
            task_processor(task)
        
        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.create_foo")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        foo = FooModel.objects.get(name=name)

        self.assertTrue(foo)

    def test_failing_task(self):
        task = failling.schedule()
    
        self.assertEqual(task.func_name, "tests.tasks.failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, 0)

        task.is_postponed = lambda: False

        with transaction.atomic():
            task_processor(task)
        
        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, 0)

    def test_failing_restarting_task(self):
        task = restarting_failling.schedule()
    
        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        task.is_postponed = lambda: False

        for _ in range(settings.MAX_RESTARTS):
            with transaction.atomic():
                task_processor(task)
        
        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.restart_attempts, settings.MAX_RESTARTS)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)


class AsyncTasksTest(TestCase):
    def test_atask_simple(self):
        task = async_add.schedule(1, 3)
    
        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        with transaction.atomic():
            task_processor(task)
        
        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        self.assertEqual(task.returned, 4)

    def test_model_task_simple(self):
        name = "FooBar"

        task = async_create_foo.schedule(name)
    
        self.assertEqual(task.func_name, "tests.tasks.async_create_foo")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        with transaction.atomic():
            task_processor(task)
        
        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        foo = FooModel.objects.get(name=name)

        self.assertTrue(foo)

    def test_failing_task(self):
        task = async_failling.schedule()
    
        self.assertEqual(task.func_name, "tests.tasks.async_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, 0)

        task.is_postponed = lambda: False

        with transaction.atomic():
            task_processor(task)
        
        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, 0)

    def test_failing_restarting_task(self):
        task = async_restarting_failling.schedule()
    
        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.restart_attempts, 0)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)

        task.is_postponed = lambda: False

        for _ in range(settings.MAX_RESTARTS):
            with transaction.atomic():
                task_processor(task)
        
        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.restart_attempts, settings.MAX_RESTARTS)
        self.assertEqual(task.restart_delay, settings.RESTART_DELAY)
        self.assertEqual(task.max_restarts, settings.MAX_RESTARTS)
