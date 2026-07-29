import { Component, OnInit, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { map, startWith, switchMap } from 'rxjs/operators';

import { InputQueueService } from '../../api/services/input-queue.service'
import { InputQueue } from '../../api/models/input-queue'
import { UserUtil } from 'src/app/user-util';

@Component({
  selector: 'app-input-queue-waiting',
  templateUrl: './input-queue-waiting.component.html',
  styleUrls: ['./input-queue-waiting.component.css']
})
export class InputQueueWaitingComponent implements OnInit {
  permission: boolean = false;
  inputQueueData: InputQueue[];
  displayedColumns: string[] = ['status_date', 'type', 'identifier', 'source'];
  isLoadingResults = true;
  resultsLength = 0;
  pageSize = 0;

  @ViewChild(MatPaginator, { static: true }) paginator: MatPaginator;

  constructor(private inputQueueService: InputQueueService,
    private userUtil: UserUtil) { }

  ngOnInit() {    
    this.userUtil.hasPerm('riport.view_inputqueue').subscribe(p =>this.permission = p);
    this.paginator.page.pipe(
      startWith({}),
      switchMap(() => {
        this.isLoadingResults = true;
        return this.getItems(this.paginator.pageIndex);
      }),
      map(data => {
        this.isLoadingResults = false;
        this.resultsLength = data.count;
        this.pageSize = data.page_size;

        return data.results;
      })
    ).subscribe(data => this.inputQueueData = data);
  }

  getItems(page) {
    return this.inputQueueService.getList("new", page + 1);
  }
}
