import { Injectable } from '@angular/core';
import { ClientConfig } from '../models/client-config';

import { BaseService } from './base.service';

@Injectable({
  providedIn: 'root'
})
export class ClientConfigService extends BaseService {
  getData() {
    return this.getRaw<ClientConfig>(this.config.clientConfig);
  }
}
