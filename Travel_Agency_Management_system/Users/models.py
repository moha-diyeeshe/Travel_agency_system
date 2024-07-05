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
    




class ErrorLogs(models.Model):
    Username = models.CharField(max_length=20, db_index=True)
    Name = models.CharField(max_length=500, db_index=True)
    Expected_error = models.CharField(max_length=500, db_index=True)
    field_error = models.CharField(max_length=500, db_index=True)
    trace_back = models.TextField(max_length=500)
    line_number = models.IntegerField(db_index=True)
    date_recorded = models.DateTimeField(auto_now_add=True, db_index=True)
    browser = models.CharField(max_length=500, db_index=True)
    ip_address = models.CharField(max_length=500, db_index=True)
    user_agent = models.TextField(max_length=500)
    Avatar = models.FileField(upload_to="errorlogs/", null=True, blank=True)

    class Meta:
        db_table = 'errorlogs'
        ordering = ['-date_recorded']




class AuditTrials(models.Model):
    Avatar = models.FileField(upload_to="trials/")
    Username = models.CharField(max_length=20)
    path = models.CharField(max_length=60, null=True, blank=True)
    Name = models.CharField(max_length=200)
    Actions = models.CharField(max_length=400)
    Module = models.CharField(max_length=400)
    date_of_action = models.DateTimeField(auto_now_add=True)
    operating_system = models.CharField(max_length=200)
    browser = models.CharField(max_length=200)
    ip_address = models.CharField(max_length=200)
    user_agent = models.TextField(max_length=200)

    class Meta:
        db_table = 'audittrials'

    def reduceActions(self):
        return f"{self.Actions[:30]}..." if len(self.Actions) > 30 else self.Actions









class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    content_type = models.CharField(max_length=255)
    object_id = models.PositiveIntegerField()
    description = models.TextField(null=True, blank=True)
    # ip_address = models.CharField(max_length=255)
    # os = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"
