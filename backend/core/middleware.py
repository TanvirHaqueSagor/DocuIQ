from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from accounts.models import Organization

def extract_subdomain(host: str, root_domain: str) -> str | None:
    h = host.split(':')[0]
    if h == root_domain:
        return None
    if h.endswith('.' + root_domain):
        return h[:-(len(root_domain)+1)].split('.')[0]
    return None

class SubdomainTenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.tenant = None
        root_domain = getattr(settings, 'ROOT_DOMAIN', 'localhost')
        sub = extract_subdomain(request.get_host(), root_domain)
        if sub:
            try:
                request.tenant = Organization.objects.get(subdomain=sub)
            except Organization.DoesNotExist:
                request.tenant = None
