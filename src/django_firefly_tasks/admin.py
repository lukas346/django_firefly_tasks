from django.contrib import admin

from django_firefly_tasks.models import TaskModel


class TaskAdmin(admin.ModelAdmin):
    pass


admin.site.register(TaskModel, TaskAdmin)
