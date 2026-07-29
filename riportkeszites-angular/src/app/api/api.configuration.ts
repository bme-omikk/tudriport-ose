import { Injectable } from '@angular/core';

@Injectable()
export class ApiConfiguration {
    rootUrl = 'https://www.example.org/tudriport-api/';
    loginUrl = 'https://www.example.org/Shibboleth.sso/Login';
    logoutUrl = 'https://www.example.org/Shibboleth.sso/Logout';

    switchLanguage = `${this.rootUrl}switch-language/{language_code}`

    user = `${this.rootUrl}user/`
    users = `${this.rootUrl}users/`
    userToggleGroup = `${this.rootUrl}user/{user}/togglegroup/{group}/`
    dashboard = `${this.rootUrl}dashboard/`

    LanguagesWithWarning = `${this.rootUrl}Language/?warning=true`
    LocationsWithWarning = `${this.rootUrl}Location/?warning=true`

    extAuthorCreateFromFile = `${this.rootUrl}ImportExtAuthorlist`

    riport = `${this.rootUrl}riport/`
    riportModes = `${this.riport}modes/`
    riportExtraFields = `${this.riport}extrafields/{mode}`
    extAuthorsSummary = `${this.riport}extauthors/{mode}/`
    extAuthorDetails = `${this.riport}detail/{mode}/`
    extAuthorAdhoc = `${this.riport}adhoc/{mode}/`

    extAuthorlistAvailable = `${this.rootUrl}Available/ExtAuthorlist/`
    extAuthorOrganizations = `${this.extAuthorlistAvailable}Organizations/`
    extAuthorUnits = `${this.extAuthorlistAvailable}Units/{org}/`
    extAuthorSubUnits = `${this.extAuthorlistAvailable}Subunits/{org}/{unit}/`
    extAuthorSubSubUnits = `${this.extAuthorlistAvailable}SubSubunits/{org}/{unit}/{subunit}/`

    extAuthorlistAuthors = `${this.extAuthorlistAvailable}Authors/`
    extAuthorlistAuthorsOrg = `${this.extAuthorlistAuthors}{org}/`
    extAuthorlistAuthorsUnit = `${this.extAuthorlistAuthors}{org}/{unit}/`
    extAuthorlistAuthorsSubunit = `${this.extAuthorlistAuthors}{org}/{unit}/{subunit}/`
    extAuthorlistAuthorsSubsubunit = `${this.extAuthorlistAuthors}{org}/{unit}/{subunit}/{subsubunit}/`

    manageExtAuthorlist = `${this.rootUrl}Manage/ExtAuthorlist/`
    deleteExtAuthorlist = `${this.rootUrl}Delete/ExtAuthorlist/{id}/`

    availableGroups = `${this.rootUrl}Available/groups`

    inputQueue = `${this.rootUrl}InputQueue/`
    inputQueueStatus = `${this.inputQueue}status`
    inputQueueAddAuthor = `${this.inputQueue}AddAuthor`
    inputQueueAddAuthors = `${this.inputQueue}AddAuthors`
    inputQueueAddPublications = `${this.inputQueue}AddPublications`

    citationDuplums = `${this.rootUrl}CitationDuplums/`
    citationDuplumsDbDatetime = `${this.rootUrl}CitationDuplums/{dbdatetime}/`    
    
    Type = `${this.rootUrl}Available/Types/`
    Typesubtypes = `${this.rootUrl}Available/Typesubtypes/`
    TypesubtypesType = `${this.rootUrl}Available/Typesubtypes/{type}/`
    Characters = `${this.rootUrl}Available/Characters/`
    clientConfig = `${this.rootUrl}clientconfig`
}
