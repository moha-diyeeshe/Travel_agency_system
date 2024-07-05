# your_app/middleware.py

from django.utils.deprecation import MiddlewareMixin

from Users.utils import log_error
from .models import AuditTrials
import logging
from user_agents import parse

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            user_agent_string = request.META.get('HTTP_USER_AGENT', 'unknown')
            user_agent = parse(user_agent_string)
            try:
                AuditTrials.objects.create(
                    Username=request.user.username,
                    path=request.path,
                    Name=request.user.get_full_name() or 'Unknown User',
                    Actions='Visited ' + request.path,
                    Module='General',
                    operating_system=user_agent.os.family + " " + user_agent.os.version_string,
                    browser=user_agent.browser.family + " " + user_agent.browser.version_string,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
                )
            except Exception as e:
                # Log exceptions to your logging framework
                log_error(request, e)
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
