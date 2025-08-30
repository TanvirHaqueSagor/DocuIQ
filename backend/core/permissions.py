from rest_framework.permissions import BasePermission

class IsInTenant(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        tenant = getattr(request, 'tenant', None)
        prof = getattr(request.user, 'userprofile', None)
        # main domain = individual zone
        if tenant is None:
            return True
        return bool(prof and prof.organization_id == getattr(tenant, 'id', None))

    def has_object_permission(self, request, view, obj):
        tenant = getattr(request, 'tenant', None)
        org_id = getattr(obj, 'organization_id', None)
        if tenant is None:
            return org_id is None
        return org_id == tenant.id
