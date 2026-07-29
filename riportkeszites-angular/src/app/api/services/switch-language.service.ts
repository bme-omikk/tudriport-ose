import { Injectable } from '@angular/core';

import { BaseService } from './base.service';
import { InputQueue } from '../models/input-queue';
import { InputQueueStatus } from '../models/input-queue-status';
import { Pageable } from '../models/pageable';

@Injectable({
  providedIn: 'root'
})
export class LanguageSwitchService extends BaseService {
  switchLanguage(language_code){
    var res = this.getRaw(this.config.switchLanguage.replace(/{language_code}/, language_code));    
    return res
  }
}
