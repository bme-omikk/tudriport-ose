from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class ExtendedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    orgId = models.TextField()
    affiliation = models.TextField()

    def __str__(self):
        return self.user.username

    class Meta:
        permissions = (
            ('view_admin_page', 'Can view angular admin page'),
            ('general_admin', 'Can view general informations on admin page'),
        )

@receiver(post_save, sender="riport.ExtendedUser")
def addDefaultGroup(sender, instance, **kwargs):
    defaultGroup = Group.objects.get(name="User")
    instance.user.groups.add(defaultGroup)
    instance.user.save()
