import { Injectable } from '@angular/core';
import { flatMap } from 'rxjs/operators';
import { Observable, of } from 'rxjs';

import { BaseService } from './base.service';
import { User } from '../models/user';
import { Pageable } from '../models/pageable';

@Injectable({
  providedIn: 'root'
})
export class UserService extends BaseService {
  getCurrentUser() {
    return this.getRaw<User>(this.config.user).pipe(flatMap(
      (user: User): Observable<User> => {
        if (!user.orgId)
          return of(null);

        return of(user);
      }
    ));
  }

  getUsers(page: number, search?: string) {
    let data = {"page": page};
    if (search) {
      data["search"] = search;
    }
    return this.getRaw<Pageable<User>>(this.config.users, data);
  }

  toggleGroup(userId: number, groupName: string) {
    let url = this.config.userToggleGroup.replace("{user}", userId.toString()).replace("{group}", groupName);
    return this.postRaw(url);
  }

  getAvailableGroups() {
    return this.getRaw<string[]>(this.config.availableGroups);
  }
}
