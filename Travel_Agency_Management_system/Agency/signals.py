# Agency/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission

from django.contrib.contenttypes.models import ContentType

from django.db.models.signals import post_save, post_delete

from Users.models import ActivityLog







@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if not sender._meta.model_name == 'activitylog':
        # Assuming your model instances have a user field
        user = getattr(instance, 'user', None)
        if user:
            action = 'created' if created else 'updated'
            ActivityLog.objects.create(
                user=user,
                action=action,
                content_type=ContentType.objects.get_for_model(sender).model,
                object_id=instance.pk,
                description=str(instance)
            )

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if not sender._meta.model_name == 'activitylog':
        # Assuming your model instances have a user field
        user = getattr(instance, 'user', None)
        if user:
            ActivityLog.objects.create(
                user=user,
                action='deleted',
                content_type=ContentType.objects.get_for_model(sender).model,
                object_id=instance.pk,
                description=str(instance)
            )