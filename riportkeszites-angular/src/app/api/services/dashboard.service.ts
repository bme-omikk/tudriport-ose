import { Injectable } from '@angular/core';

import { BaseService } from './base.service';
import { Dashboard } from '../models/dashboard';

@Injectable({
  providedIn: 'root'
})
export class DashboardService extends BaseService {
  getData() {
    return this.getRaw<Dashboard>(this.config.dashboard);
  }
}
