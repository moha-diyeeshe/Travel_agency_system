# Agency/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission

from django.contrib.contenttypes.models import ContentType

from django.db.models.signals import post_save, post_delete

from Users.models import ActivityLog

# @receiver(post_migrate)
# def create_groups_and_permissions(sender, **kwargs):
#     admin_group, created = Group.objects.get_or_create(name='Admin')
#     staff_group, created = Group.objects.get_or_create(name='Staff')

#     # Assign permissions to Admin (all permissions)
#     admin_permissions = Permission.objects.all()
#     admin_group.permissions.set(admin_permissions)

#     # Assign permissions to Staff (excluding add and change user)
#     excluded_permissions = Permission.objects.filter(codename__in=[])
#     staff_permissions = Permission.objects.exclude(pk__in=excluded_permissions)
#     staff_group.permissions.set(staff_permissions)

#     admin_group.save()
#     staff_group.save()

#     print('Successfully created Admin and Staff groups with permissions')





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