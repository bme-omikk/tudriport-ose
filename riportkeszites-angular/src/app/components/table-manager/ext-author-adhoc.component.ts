import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { ExtAuthorService } from '../../api/services/ext-author.service';
import { ClientConfigService } from '../../api/services/client-config.service';

import { Type, Typesubtype } from '../../api/models/typesubtype';
import { Character } from '../../api/models/character';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { TimeMachineSetComponent } from '../dashboard/time-machine-set.component';
import { ExtraField } from 'src/app/api/models/extra-field';
import { ExtAuthorlist } from 'src/app/api/models/ext-author';
import { NotificationManager, NotificationType } from 'src/app/notification-manager';
import { ClientConfig } from 'src/app/api/models/client-config';
import { SearchData } from './search-data';
import cloneDeep from 'lodash.clonedeep';
import { GlobalsSharedSerevice } from 'src/app/app.component';
@Component({
  selector: 'app-ext-author-adhoc',
  templateUrl: './ext-author-adhoc.component.html',
  styleUrls: ['./ext-author-adhoc.component.css']
})
export class ExtAuthorAdhocComponent implements OnInit {
  typeForm: FormGroup = this._formBuilder.group({
        typeGroup: '',
      });

  authorsLoadingInProgress: boolean = false;

  clientConfig: ClientConfig;
  actualSearchData: SearchData = new SearchData();
  lastSearchData: SearchData = new SearchData();  
  viewablepubids: string = null;  
  availableAuthors: ExtAuthorlist[] = null;
  filteredAuthors: ExtAuthorlist[] = null;
  myControl = new FormControl();
  modeChanged(){
    if(this.actualSearchData.mode) this.extAuthService.getExtraFileds(this.actualSearchData.mode).subscribe(res => {      
      this.actualSearchData.extraFields = res;
      this.viewableExtraFields = res.filter(ef => ef.views.indexOf('adhoc') > -1);
    });    
  }
  extraFields: ExtraField[] = [];
  viewableExtraFields: ExtraField[] = [];

  availableTypes : Type[] = [];
  availableTypesubtypes: Typesubtype[] = [];
  availableCharacters: Character[] = [];
  availableOrgs: string[] = null;
  availableUnits: string[] = null;
  availableSubUnits: string[] = null;
  availableSubSubUnits: string[] = null;
  availableModes: string[] = null;
  @ViewChild('tableManager', { static: true }) tableManager;

  constructor(private extAuthService: ExtAuthorService,
              private clientConfigService: ClientConfigService,
              private router: Router,
              private route: ActivatedRoute,
              private _formBuilder: FormBuilder,
              private notificationManager: NotificationManager,
              public globals: GlobalsSharedSerevice) { }
  ngOnInit() {
    this.clientConfigService.getData().subscribe(cc => this.clientConfig = cc);
    this.route.params.subscribe(params => {
      if (params.mode) {
        this.initWithParams(params);
      } else {
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

  initWithParams(params) {        
    this.extAuthService.getModes().subscribe(modes => this.availableModes = modes);   
    this.extAuthService.getExtraFileds(params.mode).subscribe(res => {
      this.actualSearchData.mode = params.mode;
      this.extraFields = res;
      this.viewableExtraFields = res.filter(ef => ef.views.indexOf('adhoc') > -1);  
      if (params.year_from) this.actualSearchData.yearFrom = params.year_from;      
      if (params.year_to) this.actualSearchData.yearTo = params.year_to;      
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
      this.addAuthors(params.mtmt);
      this.addTypes(params.type);
      if(params.type){
        this.addTypesubtypes(params.subtype); 
      }
      this.addCharacters(params.character);
      if(params.pubids){
        this.actualSearchData.pubids = params.pubids;
      } 
      this.extraFields.forEach(ef =>{
        if(params[ef.id]) ef.value = params[ef.id];
      });
      let extraParams = {}; 
      this.extraFields.forEach(ef => {
        if(ef.value) extraParams[ef.id] = ef.value;
      });
      let data = this.extAuthService.getAdhocPoints(this.actualSearchData.mode, +params.mtmt, this.actualSearchData.org, this.actualSearchData.unit, this.actualSearchData.subunit, this.actualSearchData.subsubunit, this.actualSearchData.yearFrom, this.actualSearchData.yearTo, params.type, params.subtype, params.character, this.actualSearchData.pubids, TimeMachineSetComponent.timeMachineDate, extraParams);
      this.tableManager.refreshData(data);
      data.subscribe(td => {      
        this.viewablepubids = td.additionalData;
      });      
      this.lastSearchData = cloneDeep(this.actualSearchData); 
    });
  }

  initWithoutParams() {
    this.addAuthors();
    this.addOrgs();
    this.addTypes(null);
    this.addTypesubtypes(null);
    this.addCharacters(null);
    this.extAuthService.getModes().subscribe(modes => {
      this.availableModes = modes;
      this.actualSearchData.mode = modes[0];
    });
  }

  update() {
    let route:any[] = ["riport", "adhoc", this.actualSearchData.mode]
    let params = {} 
    if(this.actualSearchData.author?.mtmtcode) {
      params['mtmt'] = this.actualSearchData.author.mtmtcode;
    }
    if (this.actualSearchData.org)
      params['org'] = this.actualSearchData.org;
    if (this.actualSearchData.unit)
      params['unit'] = this.actualSearchData.unit;
    if (this.actualSearchData.subunit)
      params['subunit'] =this.actualSearchData.subunit;
    if (this.actualSearchData.subsubunit != null)
      params['subsub_unit'] =this.actualSearchData.subsubunit;
    if (this.actualSearchData.yearFrom)
      params['year_from'] = this.actualSearchData.yearFrom;
    if (this.actualSearchData.yearTo)
      params['year_to'] = this.actualSearchData.yearTo;
    if(this.actualSearchData.typesubtype){
      params['type'] = this.actualSearchData.typesubtype.type;
      if(this.actualSearchData.typesubtype?.id){
        params['subtype'] = this.actualSearchData.typesubtype?.id;
      }
    }
    if (this.actualSearchData.character){
      params['character'] = this.actualSearchData.character.id;
    }
    if(this.actualSearchData.pubids){
      params['pubids'] = this.actualSearchData.pubids;
    }
    this.extraFields.forEach(ef => {
      if(ef.value) params[ef.id] = ef.value;
    });
    route.push(params);     
    this.router.navigate(route);
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
  updateTypesubtypes(){
    this.clearTypesubtypes();
    this.addTypesubtypes(this.actualSearchData.type?.id);
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
      }
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
  addTypes(paramType:string){
    if(paramType!=null){
      this.extAuthService.getTypes().subscribe(data => {
        this.availableTypes = data;
        this.actualSearchData.type = data.find(t=>t.id==paramType);
      });
    }
    this.extAuthService.getTypes().subscribe(data => this.availableTypes = data)    
  }
  addTypesubtypes(paramSubtype:string){
    if(paramSubtype!=null){
      this.extAuthService.getTypesubtypes(this.actualSearchData.type?.id).subscribe(data => {
        this.availableTypesubtypes = data;
        this.actualSearchData.typesubtype = data.find(t=>t.id==paramSubtype);
      });
    }
    this.extAuthService.getTypesubtypes(this.actualSearchData.type?.id).subscribe(data => this.availableTypesubtypes = data)            
  }
  addCharacters(paramCharacter:string){
    if(paramCharacter!=null){
      this.extAuthService.getCharacters().subscribe(data=>{
          this.availableCharacters = data;
          this.actualSearchData.character = data.find(c=>c.id==paramCharacter);
      });
    }
    this.extAuthService.getCharacters().subscribe(data => this.availableCharacters = data);
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
  clearTypes(){
    this.clearTypesubtypes();
    this.actualSearchData.type = null;
    this.availableTypesubtypes = null;
  }
  clearTypesubtypes(){
    this.actualSearchData.typesubtype = null;
  }
  clearCharacters(){
      this.actualSearchData.character = null;
  }
  clearAuthors(){
    this.actualSearchData.author = new ExtAuthorlist();
    this.filteredAuthors = this.availableAuthors;    
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
  }
  pubidsChanged(newValue: string){
    this.actualSearchData.pubids = newValue.replace(/\s/g, "");
  }
  private _filter(value: string): ExtAuthorlist[] {
    const filterValue = value.toLowerCase();

    return this.availableAuthors.filter(author => author.personname.toLowerCase().includes(filterValue));
  }
  openInMTMT(){    
      window.open(this.clientConfig.config.mtmt2.publication_list_view_url.replace("@@@", this.viewablepubids), "_blank");
  }
}
