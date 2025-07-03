import { Component, inject } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { UserInfo } from '../models';

import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatSnackBar } from '@angular/material/snack-bar';

import * as _ from 'lodash';
import { isNilOrEmpty, goto } from '../utils/helpers';

@Component({
  selector: 'app-header',
  imports: [MatButtonModule, MatIconModule, MatMenuModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent {
  private _snackBar = inject(MatSnackBar);
  goto = goto;
  userInfo! : UserInfo; 
  
  constructor(private dataService: DataService){}

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  ngOnInit() {
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = new UserInfo(userInfo);
      },
      error: (err: DataError) => {
        if(err.statusCode !== 401) {
          this.displayError(err.message);
        }
      }
    });
  }

  logout() {
    goto('auth/logout');
  }

  get name(): string {
    if(_.isNil(this.userInfo)){
      return "UNKNOWN";
    }
    return `${this.userInfo.firstName} ${this.userInfo.lastName}`;
  }

  get admin(): boolean {
    if(isNilOrEmpty(this.userInfo)) {
      return false
    }

    if(isNilOrEmpty(this.userInfo.admin)){
      return false;
    }

    return this.userInfo.admin;
  }
}
