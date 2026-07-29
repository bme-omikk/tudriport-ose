import { share, map } from 'rxjs/operators';
import { Injectable } from '@angular/core';
import { of, Observable } from 'rxjs';


import { User } from './api/models/user';
import { UserService } from './api/services/user.service';

@Injectable()
export class UserUtil {
    private _user_obs: Observable<User>;
    private _user: User;

    constructor(private userService: UserService) {}

    getUser() {
        if (this._user) {
            return of(this._user);
        }

        if (this._user_obs) {
            return this._user_obs;
        }

        this._user_obs = this.userService.getCurrentUser()
            .pipe(map(user => {
                this._user_obs = null;
                this._user = user;
                return user;
            })).pipe(
            share());
        return this._user_obs;
    }

    hasPerm(permission: string) : Observable<boolean> {
        return this.getUser().pipe(map(user => {
            if (user)
                return user.user.permissions.indexOf(permission) > -1;
            return false;
        }));
    }

    hasAnyPerm(permissionsToCheck: string[]) : Observable<boolean> {
        return this.getUser().pipe(map(user => {
            if (user)
                for (let p of permissionsToCheck) {
                    if (user.user.permissions.indexOf(p) > -1)
                        return true;
                }
            return false;
        }));
    }
}
