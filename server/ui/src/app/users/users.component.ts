import { Component, inject, model, signal } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { UserInfo } from '../models';
import { FormGroup, FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { isNilOrEmpty } from '../utils/helpers'
import { Validation } from '../utils/form-validators'
import * as _ from "lodash";


import {MatButtonModule} from '@angular/material/button';
import {MatSelectModule} from '@angular/material/select';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatTableModule} from '@angular/material/table';
import {MatIconModule} from '@angular/material/icon';
import {MatMenuModule} from '@angular/material/menu';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatSnackBar} from '@angular/material/snack-bar';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatTooltipModule } from '@angular/material/tooltip';

class UserInfoExt extends UserInfo {
  processing: boolean = false;
  showApiKey: boolean = false;
}

@Component({
  selector: 'app-users',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSelectModule, MatProgressSpinnerModule, MatTableModule, MatIconModule, MatMenuModule, MatCheckboxModule, MatTooltipModule],
  templateUrl: './users.component.html',
  styleUrl: './users.component.scss'
})
export class UsersComponent {
  private _snackBar = inject(MatSnackBar);
  isNilOrEmpty = isNilOrEmpty;

  loading = false;
  updating = false;
  editUserForm: FormGroup;
  changePasswordFormGroup: FormGroup;
  editingUser = false;
  addingUser = false;
  selectedUser!: UserInfoExt;
  changePassword = false;
  showPassword = false;
  showConfirmPassword = false;

  users: UserInfoExt[] = [];
  
  displayedColumns = ["email", "firstName", "lastName", "apiKey", "passwordEnabled", "admin", "actions"]
  
  constructor(private dataService: DataService, private fb: FormBuilder) { 
    this.editUserForm = this.fb.group({
      email: this.fb.control<string|null>('', Validators.required),
      firstName: this.fb.control<string|null>('', Validators.required),
      lastName: this.fb.control<string|null>('', Validators.required),
      profilePic: this.fb.control<string|null>(''),
      admin: this.fb.control<boolean>(false)
    });

    this.changePasswordFormGroup =  this.fb.group({
      password: this.fb.control<string|null>('', [Validators.required, Validators.pattern('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&]).{8,}'), Validators.minLength(10)]),
      confirmPassword: this.fb.control<string|null>('', Validators.required),
    }, { validators: [Validation.match('password', 'confirmPassword')] });
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
    console.log("Error: " + errMsg, "Close");
  }

  ngOnInit(): void {
    this.reload();
  }

  reload(always?:Function, next?: Function, error?: Function) {
    this.loading = true;
    this.dataService.getUsers().subscribe({
      next: (users: UserInfo[]) => {
        this.users = [];
        for(let i in users) {
          this.users.push(new UserInfoExt(users[i]));
        }
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.loading = false;
        if(!_.isNil(error)){
          error();
        }
        if(!_.isNil(always)){
          always();
        }
      },
      complete: () => {
        this.loading = false;
        if(!_.isNil(next)){
          next();
        }
        if(!_.isNil(always)){
          always();
        }
      }
    });
  }

  addUser(): void {
    this.selectedUser = new UserInfoExt();
    this.editUserForm.patchValue({});
    this.addingUser = true;
  }

  editUser(u: UserInfo): void {
    this.loading =true;
    this.dataService.getUser(u.id).subscribe({
      next: (user: UserInfo) => {
        this.selectedUser = new UserInfoExt(user);
        this.editUserForm.patchValue(this.selectedUser);
        this.editingUser = true;
        this.loading = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.loading = false;
      }
    })
  }

  editUserChanges(): any {
    let data: any = {};

    if(this.editUserForm.value.email != this.selectedUser.email) {
      data["email"] = this.editUserForm.value.email;
    }

    if(this.editUserForm.value.firstName != this.selectedUser.firstName) {
      data["firstName"] = this.editUserForm.value.firstName;
    }

    if(this.editUserForm.value.lastName != this.selectedUser.lastName) {
      data["lastName"] = this.editUserForm.value.lastName;
    }

    if(this.editUserForm.value.profilePic != this.selectedUser.profilePic) {
      data["profilePic"] = this.editUserForm.value.profilePic;
    }

    if(this.editUserForm.value.admin != this.selectedUser.admin) {
      data["admin"] = this.editUserForm.value.admin;
    }

    return data;
  }

  editUserHasChanges(): boolean {
    return !isNilOrEmpty(this.editUserChanges());
  }

  onEditUserSubmit(): void {
    if (this.editUserForm.valid) {
      this.updating = true;
      if(this.addingUser) {
        this.dataService.createUser(this.editUserForm.value).subscribe({
          next: (res: any) => {
            this.reload(undefined, () => {this.cancelEditUser();});
            this.updating = false;
          },
          error: (err: DataError) => {
            this.displayError(err.message);
            this.updating = false;
          }
        });
      } else {
        let changes = this.editUserChanges();
        if (!isNilOrEmpty(changes)) {
          this.dataService.updateUser(this.selectedUser.id, changes).subscribe({
            next: (res: any) => {
              this.reload(undefined, () => {this.cancelEditUser();});
              this.updating = false;
            },
            error: (err: DataError) => {
              this.displayError(err.message);
              this.updating = false;
            }
          });
        }
      }
    }
  }

  cancelEditUser(): void {
    if(this.updating) {
      return;
    }
    this.editUserForm.reset();
    this.editingUser = false;
    this.addingUser = false;
    this.selectedUser = new UserInfoExt();
  }

  deleteUser(user: UserInfo) {
    if(confirm(`Are you sure you want to delete user '${user.email}'?`)) {
      this.dataService.deleteUser(user.id).subscribe({
        next: (res: any) => {
          this.reload();
        },
        error: (err: DataError) => {
          this.displayError(err.message);
        }
      });
    }
  }

  cancelChangePassword(): void {
    if(this.selectedUser.processing) {
      return;
    }

    this.changePassword = false;
    this.selectedUser = new UserInfoExt();
    this.changePasswordFormGroup.reset();
  }

  startChangePassword(user: UserInfoExt): void {
    this.changePassword = true;
    this.selectedUser = user;
    this.changePasswordFormGroup.reset();
  }

  savePassword(): void {
    if (this.changePasswordFormGroup.invalid) {
      return;
    }
    
    this.selectedUser.processing = true;
    this.dataService.updateUser(this.selectedUser.id, {password: this.changePasswordFormGroup.value.password}).subscribe({
      next: (data: UserInfo) => {
        this.selectedUser.processing = false;
        this.reload(undefined, () => {this.cancelChangePassword();});
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.selectedUser.processing = false;
      }
    });
  }

  disablePassword(): void {
    if(confirm("Are you sure you want to disable your password?  Doing so will prevent you from logging in with username and password.  You will need to log in via Google instead.")) {
      this.selectedUser.processing = true;
      this.dataService.updateUser(this.selectedUser.id, {password: null}).subscribe({
        next: (data: UserInfo) => {
          this.selectedUser.processing = false;
          this.reload(undefined, () => {this.cancelChangePassword();});
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.selectedUser.processing = false;
        }
      });
    }
  }

  _generateAPIKey(user: UserInfoExt): void {
    user.processing = true;
    this.dataService.generateUserAPIKey(user.id).subscribe({
      next: (resp: string) => {
        user.processing = false;
        this.reload();
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        user.processing = false;
      }
    })
  }

  generateAPIKey(user: UserInfoExt): void {
    if(!isNilOrEmpty(user.apiKey)) {
      if(confirm(`Are you sure you want to regenerate API key for user ${user.email}?\n The previous key will be invalidated.`)) {
        this._generateAPIKey(user);
      }
    } else {
      this._generateAPIKey(user);
    }
  }

  deleteAPIKey(user: UserInfoExt): void {
    user.processing = true;
    if(confirm(`Are you sure you want to delete the API key for user ${user.email}?`)) {
      this.dataService.deleteUserAPIKey(user.id).subscribe({
        next: (resp: string) => {
          user.processing = false
          this.reload();
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          user.processing = false;
        }
      });
    }
  }

  toggleShowPassword() : void {
    this.showPassword = !this.showPassword;
  }

  toggleShowConfirmPassword() : void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  toggleApiKeyVisibility(user: UserInfoExt): void {
    user.showApiKey = !user.showApiKey;
  }
}
