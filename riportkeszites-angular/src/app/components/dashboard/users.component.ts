import { Component, OnInit, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatTableDataSource } from '@angular/material/table';
import { map, startWith, switchMap } from 'rxjs/operators';

import { User } from '../../api/models/user';
import { UserService } from '../../api/services/user.service';
import { Pageable } from '../../api/models/pageable'
import { NotificationManager, NotificationType } from '../../notification-manager';
import { UserUtil } from 'src/app/user-util';

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css']
})
export class UsersComponent implements OnInit {
  permission: boolean = false;
  users = new MatTableDataSource<User>();
  displayedColumns: string[] = ['username', 'orgId', 'last_name', 'first_name', 'email', 'affiliation', 'actions'];
  isLoadingResults = true;
  resultsLength = 0;
  pageSize = 0;
  search: string = "";
  availableGroups: string[];

  @ViewChild(MatPaginator, { static: true }) paginator: MatPaginator;

  constructor(private userService: UserService,
              private notificationManager: NotificationManager,
              private userUtil: UserUtil) { }

  ngOnInit() {
    this.userUtil.hasPerm('riport.change_extendeduser').subscribe(p => this.permission = p);
    this.userService.getAvailableGroups().subscribe(groups => this.availableGroups = groups)
    this.users.paginator = this.paginator;    
    this.paginator.page.pipe(
      startWith({}),
      switchMap(() => {
        this.isLoadingResults = true;
        return this.getItems();
      })
    ).subscribe(data => this.users.data = data);
  }

  getItems() {
    return this.userService
      .getUsers(this.paginator.pageIndex + 1, this.search)
      .pipe(map(data => {
        this.isLoadingResults = false;
        this.resultsLength = data.count;
        this.pageSize = data.page_size;

        return data.results;
      }));
  }

  refreshData() {
    this.isLoadingResults = true;
    this.getItems().subscribe(d => this.users.data = d);
  }

  toggleGroup(userPk: number, groupName: string) {
    this.userService.toggleGroup(userPk, groupName).subscribe(d => {
      this.notificationManager.add("Sikeres művelet!", NotificationType.success);
    });
  }
}
