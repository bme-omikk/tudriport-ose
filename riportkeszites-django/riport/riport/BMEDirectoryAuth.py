import os
from django.contrib.auth.models import User
from django.db import connection
from rest_framework import authentication
from rest_framework import exceptions
from django.middleware.csrf import CsrfViewMiddleware
from riport.models.base import ExtendedUser


def set_database_user(user):
    if user:
        username = user.username
    else:
        username = 'django:anonymus'

    os.environ['DJANGO_USER'] = username


def encode_information_from_bme_directory(text):
    return text.encode('latin-1').decode('utf-8')


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason


class BMEDirectoryAuth(authentication.BaseAuthentication):
    def authenticate(self, request):
        user = None
        meta_dict = request._request.META
        username = meta_dict.get('eppn')
        if username is not None:
            # if BME direction's user does not have permission to login
            # write check logic here and
            # raise exceptions.AuthenticationFailed('No such user')
            self.enforce_csrf(request)
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                password = User.objects.make_random_password()
                last_name = encode_information_from_bme_directory(meta_dict.get('surname'))
                first_name = encode_information_from_bme_directory(meta_dict.get('givenName'))
                user = User.objects.create_user(
                    username,
                    meta_dict.get('email'),
                    password,
                    last_name=last_name,
                    first_name=first_name
                )
                ExtendedUser.objects.create(
                    user=user,
                    orgId=meta_dict.get('niifPersonOrgID', username),
                    affiliation=meta_dict.get('affiliation')
                )
        set_database_user(user)
        if user:
            return user, None
        return None

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        reason = CSRFCheck().process_view(request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)
