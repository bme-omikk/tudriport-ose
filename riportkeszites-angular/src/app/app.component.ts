import { Component, OnInit, Injectable} from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { InputQueueStatus } from './api/models/input-queue-status';
import { InputQueueService } from './api/services/input-queue.service';
import { UserUtil } from './user-util';
import { TranslateService } from '@ngx-translate/core';
import { LanguageSwitchService } from './api/services/switch-language.service';
import { BehaviorSubject } from 'rxjs';
@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit{
  title = 'app';
  status: InputQueueStatus;
  constructor(private userUtil: UserUtil, public dialog: MatDialog, private inputQueueService: InputQueueService, private translate: TranslateService, private languageSwitchService: LanguageSwitchService, public globals: GlobalsSharedSerevice,) {
  
      // this language will be used as a fallback when a translation isn't found in the current language
      translate.setDefaultLang('hu');

      // the lang to use, if the lang isn't available, it will use the current loader to get them
      if (localStorage.getItem('language_code')) {
        translate.use(localStorage.getItem('language_code'));
      } else {
       localStorage.setItem('language_code', 'hu');
       translate.setDefaultLang('hu');
      }
  }
  show = {
    admin_page: false,
    general: false,
    users: false,
    ext_author_import: false,
    input_queue: false,
    input_queue_add: false,
    update_author: false,
    update_publication: false
  }
  loadingScreen = true;
  ngOnInit() { 
    this.userUtil.hasPerm('riport.view_admin_page').subscribe(p => {this.show.admin_page = p; this.loadingScreen = false});
    this.userUtil.hasPerm('riport.general_admin').subscribe(p => this.show.general = p);
    this.userUtil.hasPerm('riport.change_extendeduser').subscribe(p => this.show.users = p);
    this.userUtil.hasPerm('riport.add_extauthorlist').subscribe(p => this.show.ext_author_import = p);
    this.userUtil.hasAnyPerm(['riport.update_author', 'riport.update_publication']).subscribe(p => this.show.input_queue_add = p);
    this.userUtil.hasPerm('riport.view_inputqueue').subscribe(p =>{
      this.show.input_queue = p;
      if(this.show.input_queue) this.inputQueueService.getStatus().subscribe(status => this.status = status);
    });
  }
  setLang(lang: string) {
    //angular side:
    localStorage.setItem('language_code', lang);
    this.translate.use(lang);
    //django side:
    this.languageSwitchService.switchLanguage(lang);
    window.location.reload();
  }
  /*
   * Search form visibility is toggled.
   */
  toggleSearchFormVisibility() {
    this.globals.setSearchFormVisibility(!this.globals.isSearchFormVisibleSubject.getValue());
  }
}
@Injectable()
export class GlobalsSharedSerevice {
    public isSearchFormVisibleSubject = new BehaviorSubject<boolean>(true);
    public tableHasContentSubject = new BehaviorSubject<boolean>(false); 
    setSearchFormVisibility(value: boolean) {
        this.isSearchFormVisibleSubject.next(value);
    }
    setTableHasContent(value: boolean) {
      this.tableHasContentSubject.next(value);
  }
}
