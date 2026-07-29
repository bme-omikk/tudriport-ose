import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import {MatAutocompleteModule} from '@angular/material/autocomplete';

import { ExtAuthorService } from '../../api/services/ext-author.service'
import { UserUtil } from 'src/app/user-util';
import { TimeMachineSetComponent } from '../dashboard/time-machine-set.component';
import { ExtraField } from 'src/app/api/models/extra-field';
import { SearchData } from './search-data';
import cloneDeep from 'lodash.clonedeep';
import { GlobalsSharedSerevice } from 'src/app/app.component';
@Component({
  selector: 'app-ext-authors-summary',
  templateUrl: './ext-authors-summary.component.html',
  styleUrls: ['./ext-author-summary.component.css']
})
export class ExtAuthorsSummaryComponent implements OnInit {
  actualSearchData: SearchData = new SearchData();
  lastSearchData: SearchData = new SearchData();

  modeChanged(){
    if(this.actualSearchData.mode) this.extAuthService.getExtraFileds(this.actualSearchData.mode).subscribe(res => {      
      this.actualSearchData.extraFields = res;
      this.viewableExtraFields = res.filter(ef => ef.views.indexOf('summary') > -1);
    });    
  }

  isDataLoaded: boolean;

  viewableExtraFields: ExtraField[] = [];
  availableOrgs: string[] = null;
  availableUnits: string[] = null;
  availableSubUnits: string[] = null;
  availableSubSubUnits: string[] = null;
  availableModes: string[] = null;

  yearSuggestList: number[] = null;

  showAdmin: boolean = false;  
  
  @ViewChild('tableManager', { static: true }) tableManager;

  constructor(private extAuthService: ExtAuthorService,
              private router: Router,
              private route: ActivatedRoute,
              private userUtil: UserUtil,
              public globals: GlobalsSharedSerevice) { 
                let _d = new Date();
                this.yearSuggestList = [_d.getFullYear()-1, _d.getFullYear()-2, _d.getFullYear()];
              }

  ngOnInit() {
    this.userUtil.hasPerm('riport.view_admin_page').subscribe(p => {
      this.showAdmin = p;
    })
    this.route.params.subscribe(params => {
      if (params.mode) {
        this.actualSearchData.mode = this.route.snapshot.paramMap.get('mode');
        this.initWithParams(params);
      } else {
        this.initWithoutParams();
      }
    });
  }

  initWithParams(params) {    
    this.extAuthService.getModes().subscribe(modes => this.availableModes = modes);
    this.extAuthService.getExtraFileds(params.mode).subscribe(res => {
      this.actualSearchData.mode = params.mode;
      this.actualSearchData.extraFields = res;
      this.viewableExtraFields = res.filter(ef => ef.views.indexOf('summary') > -1);
      this.actualSearchData.extraFields.forEach(ef=>{
        if(params[ef.id]) ef.value = params[ef.id];
      });
      if (params.year) {
        this.actualSearchData.year = params.year;
      }
      this.addOrgs();
      if (params.org) {
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
      let extraParams = {}; 
      this.actualSearchData.extraFields.forEach(ef => {
        if(ef.value) extraParams[ef.id] = ef.value;
      });
      let data = this.extAuthService.getSummaryPoints(this.actualSearchData.mode, this.actualSearchData.org, this.actualSearchData.unit, this.actualSearchData.subunit, this.actualSearchData.subsubunit, this.actualSearchData.year, TimeMachineSetComponent.timeMachineDate, extraParams);
      this.tableManager.refreshData(data);
      this.lastSearchData = cloneDeep(this.actualSearchData);
    });
  }

  initWithoutParams() {
    this.addOrgs();
    this.extAuthService.getModes().subscribe(modes => {
      this.availableModes = modes;
      this.actualSearchData.mode = modes[0]; // autoselect first mode
      this.modeChanged();
    });
  }

  update() {
    let route:any[] = ["riport", "summary", this.actualSearchData.mode]
    let params = {}

    if (this.actualSearchData.org)
      route.push(this.actualSearchData.org);
    if (this.actualSearchData.unit)
      route.push(this.actualSearchData.unit);
    if (this.actualSearchData.subunit)
      route.push(this.actualSearchData.subunit);
    if (this.actualSearchData.subsubunit != null)
      params['subsubunit'] = this.actualSearchData.subsubunit;
    if (this.actualSearchData.year)
      params['year'] = this.actualSearchData.year;    
    this.actualSearchData.extraFields.forEach(ef => {
      if(ef.value) params[ef.id] = ef.value;
    });   
    route.push(params);
    this.router.navigate(route);
  }

  openPopup(event) {
    let route :any[] = [
      "riport",
      "detail"          
    ];
    let url:string;   
    if(event.currentTarget.getAttribute('data-mtmt-id')) {
      if(this.lastSearchData.year){
        route.push("one", this.lastSearchData.mode, event.currentTarget.getAttribute('data-mtmt-id'), this.lastSearchData.year);
      }
      else{
        route.push("one", this.lastSearchData.mode, event.currentTarget.getAttribute('data-mtmt-id'));
      }
      url = route.join("/");            
    }
    else{
      route.push("many"); 
      if(this.lastSearchData.mode != null)  route.push(this.lastSearchData.mode);    
      if(this.lastSearchData.org != null)  route.push(this.lastSearchData.org);   
      if(this.lastSearchData.unit != null)  route.push(this.lastSearchData.unit);   
      if(this.lastSearchData.subunit != null)  route.push(this.lastSearchData.subunit);   
      if(this.lastSearchData.subsubunit != null)  route.push(this.lastSearchData.subsubunit);
      url = route.join("/"); 
      if(this.lastSearchData.year) url += `;year=${this.lastSearchData.year}`;
    }
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
    this.actualSearchData.unit = null;
    this.availableSubUnits = null;
  }

  clearOrg() {
    this.clearUnits();
    this.actualSearchData.org = null;
    this.availableUnits = null;
  }
}
