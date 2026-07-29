import { Injectable } from '@angular/core';

import { BaseService } from './base.service';
import { InputQueue } from '../models/input-queue';
import { InputQueueStatus } from '../models/input-queue-status';
import { Pageable } from '../models/pageable';

@Injectable({
  providedIn: 'root'
})
export class InputQueueService extends BaseService {
  getStatus() {
    return this.getRaw<InputQueueStatus>(this.config.inputQueueStatus);
  }

  getList(filterStatus:string, page:number) {
    let data = {
      "status": filterStatus,
      "page": page
    };
    return this.getRaw<Pageable<InputQueue>>(this.config.inputQueue, data);
  }

  addAuthor(author) {
    let data = {'mtmt_id': author}
    return this.postRaw(this.config.inputQueueAddAuthor, data)
  }

  addAuthors(authorIds) {
    let data = {'mtmt_id_list': authorIds}
    return this.postRaw(this.config.inputQueueAddAuthors, data)
  }

  addPublications(publicationIds) {
    let data = {'mtmt_id_list': publicationIds}
    return this.postRaw(this.config.inputQueueAddPublications, data)
  }
}
