import { Component, OnInit } from '@angular/core';

import { Dashboard } from '../../api/models/dashboard';
import { DashboardService } from '../../api/services/dashboard.service';
import { ApiConfiguration } from '../../api/api.configuration';
import { UserUtil } from 'src/app/user-util';

@Component({
  selector: 'app-general',
  templateUrl: './general.component.html',
  styleUrls: ['./general.component.css']
})
export class GeneralComponent implements OnInit {
  permission: boolean = false;
  data: Dashboard;
  showWarning: boolean = false;

  constructor(private dashboardService: DashboardService,
              private config: ApiConfiguration,
              private userUtil: UserUtil) { }

  ngOnInit() {
    this.userUtil.hasPerm('riport.general_admin').subscribe(p => this.permission = p);
    this.dashboardService.getData().subscribe(data => this.saveData(data));
  }

  saveData(data: Dashboard) {
    this.data = data;
    this.showWarning = data.LangWarningsCount > 0 || data.LocationWarningsCount > 0;
  }
}
