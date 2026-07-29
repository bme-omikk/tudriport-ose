import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import {MatAutocompleteModule} from '@angular/material/autocomplete';

import { filter, take } from 'rxjs/operators';

import { ExtAuthorService } from '../../api/services/ext-author.service'
import { InputQueueService } from '../../api/services/input-queue.service'
import { ExtAuthorlist } from '../../api/models/ext-author';
import { ExtraField } from '../../api/models/extra-field';
import { NotificationManager, NotificationType } from '../../notification-manager'
import { FormControl } from '@angular/forms';
import { UserUtil } from 'src/app/user-util';
import { TimeMachineSetComponent } from '../dashboard/time-machine-set.component';
import { SearchData } from './search-data';
import cloneDeep from 'lodash.clonedeep';
import { GlobalsSharedSerevice } from 'src/app/app.component';
@Component({
  selector: 'app-ext-author-details',
  templateUrl: './ext-author-details.component.html',
  styleUrls: ['./ext-author-details.component.css']
})
export class ExtAuthorDetailsComponent implements OnInit{
  actualSearchData: SearchData = new SearchData();
  lastSearchData: SearchData = new SearchData();
  modeChanged(){
    if(this.actualSearchData.mode) this.extAuthService.getExtraFileds(this.actualSearchData.mode).subscribe(res => {
      this.actualSearchData.extraFields = res;
      this.viewableExtraFields = res.filter(ef => ef.views.indexOf('detail') > -1);
    });
  }
  availableModes: string[] = null;
  isDataLoaded: boolean;
  authorsLoadingInProgress: boolean = false;

  viewableExtraFields: ExtraField[] = [];

  availableOrgs: string[] = null;
  availableUnits: string[] = null;
  availableSubUnits: string[] = null;
  availableSubSubUnits: string[] = null;
  myControl = new FormControl();
  availableAuthors: ExtAuthorlist[] = null;
  filteredAuthors: ExtAuthorlist[] = null;

  yearSuggestList: number[] = null;

  showAdmin: boolean = false;
  showUpdateAuthor: boolean = false;

  @ViewChild('tableManager', { static: true }) tableManager;

  constructor(private extAuthService: ExtAuthorService,
              private inputQueueService: InputQueueService,
              private notificationManager: NotificationManager,
              private router: Router,
              private route: ActivatedRoute,
              private userUtil: UserUtil,
              public globals: GlobalsSharedSerevice) {
                let _d = new Date();
                this.yearSuggestList = [_d.getFullYear()-1, _d.getFullYear()-2, _d.getFullYear()];
              }

  refreshRoute() {
    let route : any[] = [
      "riport",
      "detail"
    ];
    let params = {};
    if(this.actualSearchData.author.mtmtcode) {
      route.push("one");
      route.push(this.actualSearchData.mode);
      route.push(this.actualSearchData.author.mtmtcode);
      if(this.actualSearchData.year) route.push(this.actualSearchData.year);
    }
    else{
      route.push("many");
      route.push(this.actualSearchData.mode);
      if(this.actualSearchData.org) route.push(this.actualSearchData.org);
      if(this.actualSearchData.unit) route.push(this.actualSearchData.unit);
      if(this.actualSearchData.subunit) route.push(this.actualSearchData.subunit);
      if(this.actualSearchData.subsubunit) route.push(this.actualSearchData.subsubunit);
      if(this.actualSearchData.year) params['year'] = this.actualSearchData.year;
    }
    this.actualSearchData.extraFields.forEach(ef => {
      if(ef.value) params[ef.id] = ef.value;
    });
    route.push(params);
    this.router.navigate(route);
  }

  refreshData(refreshRouteToo=true) {
    if (this.actualSearchData.mode) {
      if(refreshRouteToo) this.refreshRoute();
      let extraParams = {};
      this.actualSearchData.extraFields.forEach(ef => {
        if(ef.value) extraParams[ef.id] = ef.value;
      });
      let data = this.extAuthService.getExtAuthorDetails(this.actualSearchData.mode, +this.actualSearchData.author.mtmtcode, +this.actualSearchData.year, this.actualSearchData.org, this.actualSearchData.unit, this.actualSearchData.subunit, this.actualSearchData.subsubunit, TimeMachineSetComponent.timeMachineDate, extraParams);
      this.tableManager.refreshData(data);
    }
  }

  requestUpdate() {
    this.inputQueueService.addAuthor(this.actualSearchData.author.mtmtcode).subscribe(d => this.notificationManager.add("Sikeres művelet!", NotificationType.success));
  }
  openPopup(event) {
    let route :any[] = [
      "riport",
      "adhoc",
      this.lastSearchData.mode
    ];
    let url:string = route.join('/');
    if(event.currentTarget.getAttribute('data-pubids')) {
      url += `;pubids=${event.currentTarget.getAttribute('data-pubids').trim().replace('[', '').replace(']', '')}`;
    } else {
      // passing year makes sense only if no pubids were given.
      // However, if pubids were given, passing year might filter the list further.
      // This would cause unexpected result for riports using the year in a special way linke gtk_temavezeto
      if(this.lastSearchData.year) url += `;year_from=${this.lastSearchData.year};year_to=${this.lastSearchData.year}`;
    }
    if(this.lastSearchData.author.mtmtcode) url += `;mtmt=${this.lastSearchData.author.mtmtcode}`;
    if(this.lastSearchData.org) url += `;org=${this.lastSearchData.org}`;
    if(this.lastSearchData.unit) url += `;unit=${this.lastSearchData.unit}`;
    if(this.lastSearchData.subunit) url += `;subunit=${this.lastSearchData.subunit}`;
    if(this.lastSearchData.subsubunit) url += `;subsubunit=${this.lastSearchData.subsubunit}`;
    if(this.lastSearchData.extraFields){
      this.lastSearchData.extraFields.forEach(ef => {
        if(ef.value) url += `;${ef.id}=${ef.value}`;
        if(event.currentTarget.getAttribute(ef.id)) {
          url += `;${ef.id}=${event.currentTarget.getAttribute(ef.id)}`;
        }
      });
    }
    window.open(url);
  }
  ngOnInit() {
    this.userUtil.hasPerm('riport.view_admin_page').subscribe(p => {
      this.showAdmin = p;
    });
    this.userUtil.hasPerm('riport.update_author').subscribe(p => {
      this.showUpdateAuthor = p;
    });

    this.route.params.subscribe(params => {
      if(params.mode){
        this.initWithParams(params);
      }
      else{
        this.initWithoutParams();
      }
    });
    this.myControl.valueChanges.subscribe(data =>
    {
      this.filteredAuthors = this._filter(data);
      let contains = this.availableAuthors.find(a => a.personname == data)
      if(contains){
        this.actualSearchData.author = this.availableAuthors.find(a => a.personname == data);
      }
    });
  }

  initWithoutParams(){
    this.extAuthService.getModes().subscribe(modes => this.availableModes = modes);
    this.addAuthors();
    this.addOrgs();
    if(this.actualSearchData.author.mtmtcode)
      this.refreshData();
  }
  initWithParams(params){
    this.extAuthService.getModes().subscribe(modes => this.availableModes = modes);
    this.extAuthService.getExtraFileds(params.mode).subscribe(res => {
      this.actualSearchData.mode = params.mode;
      this.actualSearchData.extraFields = res;
      this.viewableExtraFields = res.filter(ef => ef.views.indexOf('detail') > -1);
      this.actualSearchData.extraFields.forEach(ef=>{
        if(params[ef.id]) ef.value = params[ef.id];
      });
      if(params.mtmt) this.actualSearchData.author.mtmtcode = params.mtmt;
      if(params.year) {
        this.actualSearchData.year = params.year;
      }
      this.addOrgs();
      if(params.org) {
        this.actualSearchData.org = params.org;
        this.addUnits();
        if (params.unit) {
          this.actualSearchData.unit = params.unit;
          this.addSubUnits();
          if (params.subunit) {
            this.actualSearchData.subunit = params.subunit;
            this.addSubSubUnits();
            if (params.subsubunit) {
              this.actualSearchData.subsubunit = params.subsubunit;
            }
          }
        }
      }
      this.addAuthors(params.mtmt);

      this.refreshData(false);
      this.tableManager.isDataLoaded.pipe(
        // do something for the first "true" value emitted. See Example 1 at: https://www.learnrxjs.io/learn-rxjs/operators/filtering/take
        filter(value => value === true ),
        take(1),
      ).subscribe(() => {
        this.globals.setSearchFormVisibility(false);
      });

      this.lastSearchData = cloneDeep(this.actualSearchData);
    });
  }
  updateAuthors(){
    this.clearAuthors();
    this.addAuthors();
  }

  updateUnits() {
    this.clearUnits();
    this.addUnits();
  }

  updateSubUnits() {
    this.clearSubUnits();
    this.addSubUnits();
  }

  updateSubSubUnits() {
    this.clearSubSubUnits();
    this.addSubSubUnits();
  }

  addAuthors(selectedMtid? : string){
    this.authorsLoadingInProgress = true;
    this.extAuthService.getAuthors(this.actualSearchData.org, this.actualSearchData.unit, this.actualSearchData.subunit, this.actualSearchData.subsubunit, TimeMachineSetComponent.timeMachineDate).subscribe(data => {
      this.filteredAuthors = this.availableAuthors = data;
      if(selectedMtid) {
        let contains = this.availableAuthors.find(a => a.mtmtcode == selectedMtid)
        if(!contains){
          this.actualSearchData.author = new ExtAuthorlist();
          this.actualSearchData.author.mtmtcode = selectedMtid;
        }
        else{
          this.actualSearchData.author = this.availableAuthors.find(a => a.mtmtcode == selectedMtid);
        }
      };
      this.authorsLoadingInProgress = false;
    });
  }
  addOrgs() {
    this.extAuthService.getOrganizations(TimeMachineSetComponent.timeMachineDate).subscribe(data => this.availableOrgs = data);
  }

  addUnits() {
    this.extAuthService.getUnits(this.actualSearchData.org, TimeMachineSetComponent.timeMachineDate).subscribe(data => this.availableUnits = data);
  }

  addSubUnits() {
    this.extAuthService.getSubUnits(this.actualSearchData.org, this.actualSearchData.unit, TimeMachineSetComponent.timeMachineDate).subscribe(data => this.availableSubUnits = data);
  }

  addSubSubUnits() {
    this.extAuthService.getSubSubUnits(this.actualSearchData.org, this.actualSearchData.unit, this.actualSearchData.subunit, TimeMachineSetComponent.timeMachineDate).subscribe(data => this.availableSubSubUnits = data);
  }

  clearSubSubUnits() {
    this.actualSearchData.subsubunit = null;
  }

  clearSubUnits() {
    this.clearSubSubUnits();
    this.actualSearchData.subunit = null;
    this.availableSubSubUnits = null;
  }

  clearUnits() {
    this.clearSubUnits();
    this.actualSearchData.unit = null
    this.availableSubUnits = null;
  }

  clearOrg() {
    this.clearUnits();
    this.actualSearchData.org = null;
    this.availableUnits = null;
  }
  clearAuthors(){
    this.actualSearchData.author = new ExtAuthorlist();
    this.filteredAuthors = this.availableAuthors;
    this.clearExtraFieldValues();
  }
  mtmtChanged(newValue: string){
    let contains = this.availableAuthors.find(a => a.mtmtcode == newValue)
    if(!contains){
      this.notificationManager.add('Az adott hierarchia beállításokhoz nem kapcsolható az MTMT azonosító.', NotificationType.warning);
      this.actualSearchData.author = new ExtAuthorlist();
      this.actualSearchData.author.mtmtcode = newValue;
    }
    else{
      this.actualSearchData.author = this.availableAuthors.find(a => a.mtmtcode == newValue);
    }
    if(this.actualSearchData.author.supervisor_mtmt_authid && this.actualSearchData.extraFields.some(ef => ef.id == 'supervisor_mtmt_authid')){
      this.actualSearchData.extraFields.find(ef => ef.id == 'supervisor_mtmt_authid').value = this.actualSearchData.author.supervisor_mtmt_authid;
      this.viewableExtraFields = this.actualSearchData.extraFields.filter(ef => ef.views.indexOf('detail') > -1);
    }
  }
  private _filter(value: string): ExtAuthorlist[] {
    const filterValue = value.toLowerCase();

    return this.availableAuthors.filter(author => author.personname.toLowerCase().includes(filterValue));
  }
  private clearExtraFieldValues(){
    this.actualSearchData.extraFields.forEach(ef => ef.value = null);
    this.viewableExtraFields = this.actualSearchData.extraFields.filter(ef => ef.views.indexOf('detail') > -1);
  }
}
