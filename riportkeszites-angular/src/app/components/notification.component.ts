import { Component, OnInit } from '@angular/core';

import { ClientConfig } from 'src/app/api/models/client-config';
import { ClientConfigService } from 'src/app/api/services/client-config.service';

import { NotificationManager, NotificationItem, NotificationType } from '../notification-manager';

@Component({
  selector: 'app-notification',
  templateUrl: './notification.component.html',
  styleUrls: ['./notification.component.css']
})
export class NotificationComponent implements OnInit {
  notifications;

  constructor(private notificationManager: NotificationManager,
              private clientConfigService: ClientConfigService) { }

  ngOnInit() {
    this.notifications = this.notificationManager.notifications;

    // add client config default notifications with no timeout, i.e. 0
    this.clientConfigService.getData().subscribe(cc => {//this.clientConfig = cc;
      const cc_notifications = cc.config.user_interface_notifications;
      for(const w of cc_notifications.error) {
        this.notificationManager.add(w, NotificationType.error, 0, true);
      }
      for(const w of cc_notifications.warning) {
        this.notificationManager.add(w, NotificationType.warning, 0, true);
      }
      for(const w of cc_notifications.info) {
        this.notificationManager.add(w, NotificationType.info, 0, true);
      }
    });
  }

  close(notification: NotificationItem) {
    this.notificationManager.close(notification);
  }
}
