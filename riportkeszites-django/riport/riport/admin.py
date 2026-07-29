from django.contrib import admin

from .models import base, external

admin.site.register(external.AuthorDb)
admin.site.register(external.AuthorDbIdentifier)
admin.site.register(external.Authortype)
admin.site.register(external.Character)
admin.site.register(external.Container)
admin.site.register(external.ExtAuthorlist)
admin.site.register(external.ExtJournalClassification)
admin.site.register(external.InputQueue)
admin.site.register(external.Language)
admin.site.register(external.Location)
admin.site.register(external.Type)
admin.site.register(external.Typesubtype)
admin.site.register(external.Publication)
admin.site.register(external.Pubauthors)
admin.site.register(external.Pubref)

admin.site.register(base.ExtendedUser)
