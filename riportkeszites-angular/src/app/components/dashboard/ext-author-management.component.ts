import { Component, Inject} from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ExtAuthorlist } from 'src/app/api/models/ext-author';
import { TimeMachineSetComponent } from '../dashboard/time-machine-set.component';
import { ExtAuthorService } from '../../api/services/ext-author.service'
import { NotificationManager, NotificationType } from 'src/app/notification-manager';
import {MatDialog, MatDialogRef, MAT_DIALOG_DATA} from '@angular/material/dialog';
import { UserUtil } from 'src/app/user-util';
@Component({
  selector: 'delete-dialog',
  templateUrl: 'delete-dialog.component.html',
})
export class DeleteDialog {

  constructor(
    public dialogRef: MatDialogRef<DeleteDialog>, @Inject(MAT_DIALOG_DATA) public data) {}

}
@Component({
    selector: 'app-ext-author-management',
    templateUrl: 'ext-author-management.component.html',
    styleUrls: ['ext-author-management.component.scss']
})
export class ExtAuthorManagementComponent{
  permission: boolean = false;
  dataSource : MatTableDataSource<ExtAuthorlist> = new MatTableDataSource<ExtAuthorlist>();
  displayedColumns: string[] = ['mtmtcode', 'personname', 'weighting', 'neptuncode', 'role', 'supervisor_mtmt_authid', 'for_rollup', 'save', 'delete'];
  org: string;
  unit: string;
  subunit: string;
  subsubunit: string;
  givenMtid: string;
  header: string;
  listSubhierarchy: boolean;
  dataLoaded: boolean = true;

  authors: ExtAuthorlist[];
  listableAuthors: ExtAuthorlist[];
  availableOrgs: string[] = null;
  availableUnits: string[] = null;
  availableSubUnits: string[] = null;
  availableSubSubUnits: string[] = null;
  constructor(private extAuthService: ExtAuthorService, public dialog: MatDialog, private notificationManager: NotificationManager,
    private userUtil: UserUtil){}
  ngOnInit() {
    this.addOrgs();
    this.userUtil.hasPerm('riport.view_admin_page').subscribe(p => this.permission = p);
  }
  getAuthors(){
    this.dataLoaded = false;
    this.dataSource = new MatTableDataSource<ExtAuthorlist>();
    this.extAuthService.getAuthors(this.org, this.unit, this.subunit, this.subsubunit, TimeMachineSetComponent.timeMachineDate)
      .subscribe(data => {                
        this.displayedColumns = ['mtmtcode', 'personname', 'weighting', 'neptuncode', 'role', 'supervisor_mtmt_authid', 'for_rollup', 'save', 'delete'];
        this.authors = data;                
        if(this.listSubhierarchy){
          this.listableAuthors = this.authors;          
          if(this.subunit) this.displayedColumns.unshift('subsubunit');          
          else if(this.unit) this.displayedColumns.unshift('subunit', 'subsubunit');          
          else if(this.org) this.displayedColumns.unshift('unit', 'subunit', 'subsubunit');
          else this.displayedColumns.unshift('org', 'unit', 'subunit', 'subsubunit');
        }
        else{
          this.listableAuthors = this.authors.filter(a =>
            (a.org == this.org || (a.org == "" && this.org == null)) &&
            (a.unit == this.unit || (a.unit == "" && this.unit == null)) && 
            (a.subunit == this.subunit || (a.subunit == "" && this.subunit == null)) && 
            (a.subsub_unit == this.subsubunit || (a.subsub_unit == "" && this.subsubunit == null))           
          );
        }
        this.dataSource = new MatTableDataSource<ExtAuthorlist>(this.listableAuthors);
        this.dataLoaded = true;
      });
    
  }
  saveAuthor(author: ExtAuthorlist){
    if(!this.validateAuthor(author)) return;
    if(author.id == ''){
      this.extAuthService.postExtAuthorlist(author).subscribe(a => {        
        author.id = a.id;
        this.dataSource.data = this.dataSource.data;
      });
    }
    else{
      this.extAuthService.putExtAuthorlist(author).subscribe(a => {
        author.id = a.id;
        this.dataSource.data = this.dataSource.data;
      });
    }    
  }
  addAuthor(){
    let extAuthor: ExtAuthorlist = new ExtAuthorlist()
    extAuthor.mtmtcode = this.givenMtid;
    extAuthor.org = this.org;
    extAuthor.unit = this.unit;
    extAuthor.subunit = this.subunit;
    extAuthor.subsub_unit = this.subsubunit ?? '';
    this.dataSource.data.unshift(extAuthor);
    this.dataSource.data = this.dataSource.data;
  }
  deleteAuthor(author: ExtAuthorlist){  
    const dialogRef = this.dialog.open(DeleteDialog,
      {
        data: author
      });

    dialogRef.afterClosed().subscribe(result => {
      if(result){
        this.extAuthService.deleteExtAuthorlist(author).subscribe();
        this.dataSource.data.splice(this.dataSource.data.indexOf(author), 1);
        this.dataSource.data = this.dataSource.data;
      }      
    });
  }
  validateAuthor(author: ExtAuthorlist) : boolean{
    if(!author.mtmtcode){
      this.notificationManager.add("Az Mtid kötelezően kitöltendő mező!", NotificationType.error);
      return false;
    }
    if(isNaN(+author.mtmtcode)){
      this.notificationManager.add("Az Mtid szám kell, hogy legyen!", NotificationType.error);
      return false;
    }
    if(isNaN(+author.weighting)){
      this.notificationManager.add("Az Hozzájárulás szám kell, hogy legyen!", NotificationType.error);
      return false;
    }
    return true;
  }
  updateHeader(){
    this.header = this.org ? `${ this.org }` : "";
    this.header += this.unit ? `/${ this.unit }` : "";
    this.header += this.subunit ? `/${ this.subunit }` : "";
    this.header += this.subsubunit ? `/${ this.subsubunit }` : "";
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
    this.extAuthService.getUnits(this.org, TimeMachineSetComponent.timeMachineDate).subscribe(data => this.availableUnits = data);
  }

  addSubUnits() {
    this.extAuthService.getSubUnits(this.org, this.unit, TimeMachineSetComponent.timeMachineDate).subscribe(data => this.availableSubUnits = data);
  }

  addSubSubUnits() {
    this.extAuthService.getSubSubUnits(this.org, this.unit, this.subunit, TimeMachineSetComponent.timeMachineDate).subscribe(data => this.availableSubSubUnits = data);
  }

  clearSubSubUnits() {
    this.subsubunit = null;
  }

  clearSubUnits() {
    this.clearSubSubUnits();
    this.subunit = null;
    this.availableSubSubUnits = null;
  }

  clearUnits() {
    this.clearSubUnits();
    this.unit = null
    this.availableSubUnits = null;
  }

  clearOrg() {
    this.clearUnits();
    this.org = null;
    this.availableUnits = null;
  }
}