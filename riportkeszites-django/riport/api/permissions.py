from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated


class ExtendedDjangoModelPermissions(DjangoModelPermissions):
    """
    Revoke default read right
    """

    override_perms = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
    }

    def __init__(self):
        self.perms_map.update(self.override_perms)


class PermissionBasedPermission(IsAuthenticated):
    permission_required = None

    def __init__(self, permissions):
        self.permission_required = permissions

    def has_permission(self, request, view):
        return request.user.has_perm(self.permission_required)
