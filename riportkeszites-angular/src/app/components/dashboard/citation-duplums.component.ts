import { Component, AfterViewInit, ViewChild, OnInit} from '@angular/core';
import { ExtAuthorService } from 'src/app/api/services/ext-author.service';
import { finalize } from 'rxjs/operators';
import { CitationDuplum} from 'src/app/api/models/citation-duplum';
import { TimeMachineSetComponent } from './time-machine-set.component';
import { MatPaginator } from '@angular/material/paginator';
import { MatTableDataSource } from '@angular/material/table';
import { ClientConfigService } from 'src/app/api/services/client-config.service';
import { ClientConfig } from 'src/app/api/models/client-config';
import { UserUtil } from 'src/app/user-util';
export class TriState{
  private _true: boolean;
  private _dontcare: boolean;
  private _false: boolean; 
  public get true(){
    return this._true;
  } 
  public get dontcare(){
    return this._dontcare;
  } 
  public get false(){
    return this._false;
  }   
  public setTrue(){
    this._true = true;
    this._dontcare = false;
    this._false = false;
  }
  public setDontcare(){
    this._true = false;
    this._dontcare = true;
    this._false = false;
  }
  public setFalse(){
    this._true = false;
    this._dontcare = false;
    this._false = true;
  }
}
@Component({
    selector: 'app-citation-duplums',
    templateUrl: 'citation-duplums.component.html',
    styleUrls: ['citation-duplums.component.css']
})
export class CitationDuplumsComponent implements OnInit{  
  permission: boolean = false;
  private clientConfig: ClientConfig;
  dataSource : MatTableDataSource<CitationDuplum>;
  searching = false;  
  citationDuplums: CitationDuplum[];
  filteredDuplums: CitationDuplum[];
  displayedColumns: string[] = ['mtmt_pubid', 'label_txt', 'doi', 'title', 'errors']; 
  
  duplicateDoi: TriState = new TriState();
  duplicateTitle: TriState = new TriState();
  notPublished: TriState = new TriState();
  citingDocNotPublished: TriState = new TriState();
  citingDocWError: TriState = new TriState();
  unknownExternal: TriState = new TriState();

  @ViewChild(MatPaginator) paginator: MatPaginator;

  constructor(private extAuthService: ExtAuthorService, 
              private clientConfigService: ClientConfigService,
              private userUtil: UserUtil) { 
    this.duplicateDoi.setTrue();
    this.duplicateTitle.setDontcare();
    this.notPublished.setDontcare();
    this.citingDocNotPublished.setDontcare();
    this.citingDocWError.setDontcare();
    this.unknownExternal.setDontcare();
  }
  ngOnInit() {
    this.userUtil.hasPerm('riport.view_admin_page').subscribe(p => this.permission = p);
    this.clientConfigService.getData().subscribe(cc => this.clientConfig = cc);
  }
  search() {
    this.searching = true;
    //this.displayedColumns = ['mtmt_pubid', 'label_txt', 'doi', 'title', 'errors'];
    this.extAuthService.getCitationDuplums(TimeMachineSetComponent.timeMachineDate).pipe(finalize(() => this.searching = false)).subscribe(data => {
      this.citationDuplums = data;
      this.filterDuplums();      
    });
  }
  openDoi(doi:string) {    
    window.open(this.clientConfig.config.doi.replace("@@@", doi), "_blank");
  }
  openCitationsInMTMT(mtids:string){
    window.open(this.clientConfig.config.mtmt2.citation_list_view_url.replace("@@@", mtids), "_blank");
  }

  filterDuplums(){
    this.filteredDuplums = this.citationDuplums;
    if(this.duplicateDoi.true) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_duplicate_doi_info.length > 0)  
    if(this.duplicateDoi.false) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_duplicate_doi_info.length == 0)  
    if(this.duplicateTitle.true) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_duplicate_title_info.length > 0)  
    if(this.duplicateTitle.false) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_duplicate_title_info.length == 0)  
    if(this.notPublished.true) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_list_not_published.length > 0)  
    if(this.notPublished.false) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_list_not_published.length == 0)  
    if(this.citingDocNotPublished.true) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_list_citingdoc_not_published.length > 0)  
    if(this.citingDocNotPublished.false) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_list_citingdoc_not_published.length == 0)  
    if(this.citingDocWError.true) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_list_citingdoc_w_error.length > 0)  
    if(this.citingDocWError.false) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_list_citingdoc_w_error.length == 0)  
    if(this.unknownExternal.true) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_list_unknown_external.length > 0)  
    if(this.unknownExternal.false) this.filteredDuplums = this.filteredDuplums.filter(duplum => duplum.citation_list_unknown_external.length == 0)
    this.dataSource = new MatTableDataSource<CitationDuplum>(this.filteredDuplums);
    this.dataSource.paginator = this.paginator;
  }

  nextState(triState:TriState){
    if(triState.true){
      triState.setFalse();
      return;
    }
    if(triState.dontcare){
      triState.setTrue();
      return;
    }
    if(triState.false){
      triState.setDontcare();
      return;
    }
  }
}
