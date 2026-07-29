import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { GeneralComponent }  from './components/dashboard/general.component';
import { UsersComponent }  from './components/dashboard/users.component';
import { ExtAuthorImportComponent}  from './components/dashboard/ext-author-import.component';
import { ExtAuthorManagementComponent }  from './components/dashboard/ext-author-management.component';
import { InputQueueWaitingComponent }  from './components/dashboard/input-queue-waiting.component';
import { InputQueueAddComponent }  from './components/dashboard/input-queue-add.component';
import { CitationDuplumsComponent }  from './components/dashboard/citation-duplums.component';
import { TimeMachineSetComponent }  from './components/dashboard/time-machine-set.component';
import { ExtAuthorsSummaryComponent } from './components/table-manager/ext-authors-summary.component';
import { ExtAuthorDetailsComponent } from './components/table-manager/ext-author-details.component';
import { ExtAuthorAdhocComponent } from './components/table-manager/ext-author-adhoc.component';

const routes: Routes = [
  { path: '', component: ExtAuthorsSummaryComponent, pathMatch: 'full' },

  { path: 'riport/summary', component: ExtAuthorsSummaryComponent},
  { path: 'riport/summary/:mode', component: ExtAuthorsSummaryComponent},
  { path: 'riport/summary/:mode/:org', component: ExtAuthorsSummaryComponent},
  { path: 'riport/summary/:mode/:org/:unit', component: ExtAuthorsSummaryComponent},
  { path: 'riport/summary/:mode/:org/:unit/:subunit', component: ExtAuthorsSummaryComponent},
  { path: 'riport/summary/:mode/:org/:unit/:subunit/:subsubunit', component: ExtAuthorsSummaryComponent},

  { path: 'riport/detail', component: ExtAuthorDetailsComponent},
  { path: 'riport/detail/:mode', component: ExtAuthorDetailsComponent},
  { path: 'riport/detail/one/:mode/:mtmt', component: ExtAuthorDetailsComponent},
  { path: 'riport/detail/one/:mode/:mtmt/:year', component: ExtAuthorDetailsComponent},
  { path: 'riport/detail/many/:mode/:org', component: ExtAuthorDetailsComponent},
  { path: 'riport/detail/many/:mode/:org/:unit', component: ExtAuthorDetailsComponent},
  { path: 'riport/detail/many/:mode/:org/:unit/:subunit', component: ExtAuthorDetailsComponent},
  { path: 'riport/detail/many/:mode/:org/:unit/:subunit/:subsubunit', component: ExtAuthorDetailsComponent},

  { path: 'dashboard/general', component: GeneralComponent},
  { path: 'dashboard/users', component: UsersComponent},
  { path: 'dashboard/extauthorimport', component: ExtAuthorImportComponent},
  { path: 'dashboard/extauthormanagement', component: ExtAuthorManagementComponent},
  { path: 'dashboard/inputqueuewaiting', component: InputQueueWaitingComponent},
  { path: 'dashboard/inputqueueadd', component: InputQueueAddComponent},
  { path: 'dashboard/citationduplums', component: CitationDuplumsComponent},
  { path: 'dashboard/timemachineset', component: TimeMachineSetComponent},

  { path: 'riport/adhoc', component: ExtAuthorAdhocComponent},
  { path: 'riport/adhoc/:mode', component: ExtAuthorAdhocComponent},
];

@NgModule({
  exports: [ RouterModule ],
  imports: [ RouterModule.forRoot(routes) ],
})
export class AppRoutingModule { }
