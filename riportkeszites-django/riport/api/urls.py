from django.conf.urls import include
from django.urls import path, re_path
from rest_framework import routers

from api.views.base import (InputQueueViewSet,
                            LocationViewSet, LanguageViewSet, ExtendedUsersViewSet)
from api.views.extended import (ManageExtAuthor, ImportExtAuthorlist, InputQueueAddAuthor, InputQueueAddPublication, AvailableOrganizations,
                                AvailableUnits, AvailableSubUnits, AuthenticatedUser, DashboardGeneral, SwitchLanguage, ToggleUserGroup,
                                AvailableSubSubUnits, AvailablePointModes, InputQueueStatusView, InputQueueAddAuthors,
                                AvailableGroups, AvailableAuthors, CitationDuplums, AvailableCharacters, AvailableTypes, AvailableTypesubtypes, ExtraFields, ClientConfig)
from api.views.template import AuthorListView, AuthorDetailView, AuthorAdhocView


router = routers.DefaultRouter()
router.include_root_view = False
router.register('InputQueue', InputQueueViewSet)
router.register('Language', LanguageViewSet)
router.register('Location', LocationViewSet)
router.register('users', ExtendedUsersViewSet)


urlpatterns = [
    path('', include(router.urls)),

    path('switch-language/<str:language_code>/', SwitchLanguage.as_view()),

    path('user/', AuthenticatedUser.as_view()),
    path('user/<int:user>/togglegroup/<str:group>/', ToggleUserGroup.as_view()),
    path('dashboard/', DashboardGeneral.as_view()),

    path('clientconfig', ClientConfig.as_view()),

    path('ImportExtAuthorlist', ImportExtAuthorlist.as_view()),

    path('riport/modes/', AvailablePointModes.as_view()),
    path('riport/extauthors/<str:mode>/', AuthorListView.as_view()),
    path('riport/extauthors/<str:mode>/<str:org>/', AuthorListView.as_view()),
    path('riport/extauthors/<str:mode>/<str:org>/<str:unit>/', AuthorListView.as_view()),
    path('riport/extauthors/<str:mode>/<str:org>/<str:unit>/<str:subunit>/', AuthorListView.as_view()),
    re_path(r'riport/extauthors/(?P<mode>\w+)/(?P<org>\w+)/(?P<unit>\w+)/(?P<subunit>\w+)/(?P<subsub_unit>\w*)/', AuthorListView.as_view()),   

    path('riport/detail/<str:mode>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<int:mtmt_id>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<int:mtmt_id>/<int:year>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<str:org>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<str:org>/<int:year>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<str:org>/<str:unit>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<str:org>/<str:unit>/<int:year>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<str:org>/<str:unit>/<str:subunit>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<str:org>/<str:unit>/<str:subunit>/<int:year>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<str:org>/<str:unit>/<str:subunit>/<str:subsubunit>/', AuthorDetailView.as_view()),
    path('riport/detail/<str:mode>/<str:org>/<str:unit>/<str:subunit>/<str:subsubunit>/<int:year>/', AuthorDetailView.as_view()),

    path('riport/extrafields/<str:mode>', ExtraFields.as_view()),

    path('InputQueue/status', InputQueueStatusView.as_view()),
    path('InputQueue/AddAuthor', InputQueueAddAuthor.as_view()),
    path('InputQueue/AddAuthors', InputQueueAddAuthors.as_view()),
    path('InputQueue/AddPublications', InputQueueAddPublication.as_view()),

    path('Available/ExtAuthorlist/Organizations/', AvailableOrganizations.as_view()),
    path('Available/ExtAuthorlist/Units/<str:org>/', AvailableUnits.as_view()),
    path('Available/ExtAuthorlist/Subunits/<str:org>/<str:unit>/', AvailableSubUnits.as_view()),
    path('Available/ExtAuthorlist/SubSubunits/<str:org>/<str:unit>/<str:subunit>/', AvailableSubSubUnits.as_view()),
    path('Available/groups', AvailableGroups.as_view()),
    
    path('Available/ExtAuthorlist/Authors/', AvailableAuthors.as_view()),
    path('Available/ExtAuthorlist/Authors/<str:org>/', AvailableAuthors.as_view()),
    path('Available/ExtAuthorlist/Authors/<str:org>/<str:unit>/', AvailableAuthors.as_view()),
    path('Available/ExtAuthorlist/Authors/<str:org>/<str:unit>/<str:subunit>/', AvailableAuthors.as_view()),
    path('Available/ExtAuthorlist/Authors/<str:org>/<str:unit>/<str:subunit>/<str:subsubunit>/', AvailableAuthors.as_view()),

    path('Manage/ExtAuthorlist/', ManageExtAuthor.as_view()),
    path('Delete/ExtAuthorlist/<int:id>/', ManageExtAuthor.as_view()),

    path('CitationDuplums/', CitationDuplums.as_view()),
    path('CitationDuplums/<str:dbdatetime>/', CitationDuplums.as_view()),

    path('Available/Types/', AvailableTypes.as_view()),
    path('Available/Typesubtypes/', AvailableTypesubtypes.as_view()),
    path('Available/Typesubtypes/<str:type>/', AvailableTypesubtypes.as_view()),
    path('Available/Characters/', AvailableCharacters.as_view()),

    path('riport/adhoc/<str:mode>/', AuthorAdhocView.as_view())
]
