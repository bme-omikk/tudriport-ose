import { Injectable } from '@angular/core';

const defaultTimeout = 4000;

export enum NotificationType {
    info,
    success,
    warning,
    error
}

export class NotificationItem {

    constructor(
        private id: number,
        private text: string,
        private type: NotificationType,
        private timeout: number,
        private isHTML: boolean,
    ) { }
}

@Injectable()
export class NotificationManager {
    notifications: NotificationItem[] = [];
    nextId:number = 0;

    public add(text: string, type: NotificationType = NotificationType.info, timeout: number = defaultTimeout, isHTML: boolean = false) {
        let notification = new NotificationItem(this.nextId++, text, type, timeout, isHTML);
        this.notifications.push(notification);
        if (timeout > 0) {
            setTimeout(
                () => this.close(notification),
                timeout);
        }
    }

    public close(notification: NotificationItem) {
        let position = this.notifications.indexOf(notification);
        if (position != -1)
            this.notifications.splice(position, 1)
    }
}