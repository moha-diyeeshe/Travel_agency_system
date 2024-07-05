from .models import ActivityLog

def activity_notifications(request):
    notifications = ActivityLog.objects.order_by('-timestamp')[:16]
    return {'notifications': notifications}
