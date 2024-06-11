from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core import signing
from django.utils import timezone

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    modified_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # No required fields besides email, which is the username field.

    class Meta:
        db_table = 'users'
        ordering = ('-username',)
        permissions = [
            ('manage_role_groups', 'Can Add Or Delete Role From The Group'),
            ('remove_role_from_group', 'Can Remove Role From Group'),
            ('assign_user_to_group', 'Can Assign User To Group'),
            ('role_report', 'Can See Roles Report'),
            ('view_dashboard', 'Can view dashboard'),
        ]

    def encrypt_id(self):
        """Returns a securely encrypted ID for the user using Django's signing."""
        return signing.dumps(self.id)
    
    def get_full_name(self):
        """Returns the full name of the user."""
        return f"{self.first_name} {self.last_name}"
    










class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    content_type = models.CharField(max_length=255)
    object_id = models.PositiveIntegerField()
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"
