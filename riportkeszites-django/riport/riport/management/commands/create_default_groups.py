from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = """ Creates all default groups with default permissions. Permissions are created during migration!"""

    def get_permissions(self, list):
        return [Permission.objects.get(codename=p, content_type__app_label="riport")
                for p in list]

    def create_groups_with_perms(self):
        admin, _ = Group.objects.get_or_create(name="Admin")
        subUnitAdmin, _ = Group.objects.get_or_create(name="SubUnitAdmin")
        user, _ = Group.objects.get_or_create(name="User")

        try:
            user.permissions.add(*self.get_permissions([                
                'view_inputqueue',
            ]))

            subUnitAdmin.permissions.add(*self.get_permissions([
                'add_extauthorlist',
                'view_language',
                'view_location',
                'general_admin',
            ]))

            admin.permissions.add(*self.get_permissions([
                'change_extendeduser',                
                'view_admin_page',
                'change_language',
                'change_location',
                'update_publication',
                'update_author',
                'add_extauthorlist',
                'view_language',
                'view_location',
                'general_admin',
            ]))
            self.stdout.write(self.style.SUCCESS("Done."))

        except Permission.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(
                "Operation aborted! One or more permission does not exist. Were necessary migrations ran before this command? %s" % e
            ))

    def handle(self, *args, **options):
        self.create_groups_with_perms()
