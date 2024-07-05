import sys
import os
import traceback
from django.conf import settings
from .models import ErrorLogs
from user_agents import parse


def log_error(request, e):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    user_agent_string = request.META.get('HTTP_USER_AGENT', 'unknown')
    user_agent = parse(user_agent_string)
    ErrorLogs.objects.create(
        Username=request.user.username if request.user.is_authenticated else 'Anonymous',
        Name="Error in Django View",
        Expected_error=str(exc_type),
        field_error=str(e),
        trace_back=''.join(traceback.format_exception(exc_type, exc_obj, exc_tb)),
        line_number=exc_tb.tb_lineno,
        browser=user_agent.browser.family + " " + user_agent.browser.version_string,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),

    )

