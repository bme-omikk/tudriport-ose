import { Component, OnInit } from '@angular/core';

import { InputQueueService } from '../../api/services/input-queue.service'
import { Pageable } from '../../api/models/pageable'
import { NotificationManager, NotificationType } from '../../notification-manager'
import { UserUtil } from '../../user-util';

@Component({
  selector: 'app-input-queue-add',
  templateUrl: './input-queue-add.component.html',
  styleUrls: ['./input-queue-add.component.css']
})
export class InputQueueAddComponent implements OnInit {
  pattern = new RegExp("^([0-9]+)(,[0-9]+)*$");
  publicationIds = "";
  authorIds = "";
  isValidPubs = true;
  isValidAuthors = true;
  show = {
    update_author: false,
    update_publication: false
  }

  constructor(private inputQueueService: InputQueueService,
              private notificationManager: NotificationManager,
              private userUtil: UserUtil) { }

  ngOnInit() {
    this.userUtil.hasPerm('riport.update_author').subscribe(p => this.show.update_author = p);
    this.userUtil.hasPerm('riport.update_publication').subscribe(p => this.show.update_publication = p);
  }

  validate_publications() {
    return this.isValidPubs = this.pattern.test(this.publicationIds);
  }

  validate_authors() {
    return this.isValidAuthors = this.pattern.test(this.authorIds);
  }

  submit_publications() {
    if (this.validate_publications()) {
      let list = this.publicationIds.split(',').map(id => parseInt(id));

      this.inputQueueService.addPublications(list).subscribe(result => {
        if (this.handleResponse(result))
          this.publicationIds = "";
      });
    }
  }

  submit_authors() {
    if (this.validate_authors()) {
      let list = this.authorIds.split(',').map(id => parseInt(id));

      this.inputQueueService.addAuthors(list).subscribe(result => {
        if (this.handleResponse(result))
          this.authorIds = "";
      });
    }
  }

  handleResponse(result) {
    if (result) {
      this.notificationManager.add("Hiba: " + result["mtmt_id_list"][0], NotificationType.error, 5000);
      return false;
    }

    this.notificationManager.add("Sikeres művelet!", NotificationType.success);
    return true;
  }
}
