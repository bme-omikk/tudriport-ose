import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { BrowserModule } from '@angular/platform-browser';
import { APP_INITIALIZER, NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { DataTablesModule } from "angular-datatables";

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatMenuModule } from '@angular/material/menu';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatAutocompleteModule} from '@angular/material/autocomplete'
import { MatCheckboxModule } from '@angular/material/checkbox';
import { ReactiveFormsModule } from '@angular/forms';

import { AppComponent, GlobalsSharedSerevice } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { ExtAuthorImportComponent } from './components/dashboard/ext-author-import.component';
import { ApiModule } from './api/api.module';
import { ExtAuthorDetailsComponent } from './components/table-manager/ext-author-details.component';
import { ExtAuthorsSummaryComponent } from './components/table-manager/ext-authors-summary.component';
import { TableManagerComponent } from './components/table-manager/table-manager.component';
import { InputQueueWaitingComponent } from './components/dashboard/input-queue-waiting.component';
import { InputQueueAddComponent } from './components/dashboard/input-queue-add.component';
import { CitationDuplumsComponent } from './components/dashboard/citation-duplums.component';
import { ExtAuthorManagementComponent, DeleteDialog } from './components/dashboard/ext-author-management.component';
import { TimeMachineSetComponent } from './components/dashboard/time-machine-set.component';
import { UserManagerComponent } from './components/user-manager.component';
import { NotificationComponent } from './components/notification.component';
import { NotificationManager } from './notification-manager';
import { UserUtil } from './user-util';
import { GeneralComponent } from './components/dashboard/general.component';
import { UsersComponent } from './components/dashboard/users.component';
import { ExtAuthorAdhocComponent } from './components/table-manager/ext-author-adhoc.component';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { TranslateService } from './translate.service';
import { TranslateModule, TranslateLoader} from '@ngx-translate/core';
import { TranslateHttpLoader} from '@ngx-translate/http-loader';
import { HttpClient } from '@angular/common/http';

export function setupTranslateServiceFactory(
  service: TranslateService): Function {
  return () => service.use('hu');
}
export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http);
}
export function createTranslateLoader(http: HttpClient) {
  return new TranslateHttpLoader(http, './assets/i18n/', '.json');
}
@NgModule({
  declarations: [
    AppComponent,    
    CitationDuplumsComponent,
    DeleteDialog,
    ExtAuthorAdhocComponent,
    ExtAuthorImportComponent,
    ExtAuthorDetailsComponent,
    ExtAuthorManagementComponent,
    ExtAuthorsSummaryComponent,
    TableManagerComponent,
    InputQueueWaitingComponent,
    InputQueueAddComponent,
    UserManagerComponent,
    NotificationComponent,
    GeneralComponent,
    TimeMachineSetComponent,
    UsersComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    ClipboardModule,
    FormsModule,

    DataTablesModule,

    MatIconModule,
    MatMenuModule,
    MatToolbarModule,
    MatButtonModule,
    MatDialogModule,
    MatSidenavModule,
    MatCardModule,
    MatProgressBarModule,
    MatInputModule,
    ReactiveFormsModule,
    MatExpansionModule,
    MatTooltipModule,
    MatTabsModule,
    MatTableModule,
    MatPaginatorModule,
    MatSelectModule,
    MatAutocompleteModule,
    MatCheckboxModule,
    ApiModule,
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: (createTranslateLoader),
        deps: [HttpClient],
      },
      defaultLanguage: localStorage.getItem('locale') || 'hu',
    })
  ],
  providers: [NotificationManager, UserUtil, GlobalsSharedSerevice],
  bootstrap: [AppComponent],
  entryComponents: [ExtAuthorDetailsComponent]
})
export class AppModule { }
