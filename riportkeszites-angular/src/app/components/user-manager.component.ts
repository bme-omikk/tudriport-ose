import { Component, OnInit } from '@angular/core';

import { ApiConfiguration } from '../api/api.configuration';
import { UserUtil } from '../user-util';
import { User } from '../api/models/user';

@Component({
  selector: 'app-user-manager',
  templateUrl: './user-manager.component.html',
  styleUrls: ['./user-manager.component.css']
})
export class UserManagerComponent implements OnInit {
  user: User;
  working: boolean = true;

  constructor(private config: ApiConfiguration,
              private userUtil: UserUtil) { }

  ngOnInit() {
      this.userUtil.getUser().subscribe(user => {this.user = user; this.working = false});
  }

  login() {
    window.location.href = `${this.config.loginUrl}?target=${window.location.href}`;
  }

  logout() {
      window.location.href = this.config.logoutUrl;
  }
}
