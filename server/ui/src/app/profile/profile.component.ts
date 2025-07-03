import { Component, inject, model, signal } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { Device, DeviceState, UserInfo } from '../models';
import { FormGroup, FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { isNilOrEmpty } from '../utils/helpers'
import { Validation } from '../utils/form-validators';
import * as _ from "lodash";


import {MatButtonModule} from '@angular/material/button';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatSnackBar} from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-profile',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatProgressSpinnerModule, MatIconModule, MatTooltipModule],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.scss'
})
export class ProfileComponent {
  private _snackBar = inject(MatSnackBar);
  userInfo: UserInfo = new UserInfo();
  editing = false;
  changePassword = false;
  processing = false;
  editFormGroup: FormGroup;
  changePasswordFormGroup: FormGroup;
  showPassword = false;
  showConfirmPassword = false;

  isNilOrEmpty = isNilOrEmpty;
  _ = _;

  newPassword: string= "";
  confirmNewPassword: string = "";

  constructor(private dataService: DataService, private fb: FormBuilder) {
    this.editFormGroup = this.fb.group({
      email: this.fb.control<string|null>('', Validators.required),
      firstName: this.fb.control<string|null>('', Validators.required),
      lastName: this.fb.control<string|null>('', Validators.required),
      profilePic: ['']
    });

    this.changePasswordFormGroup =  this.fb.group({
      password: this.fb.control<string|null>('', [Validators.required, Validators.pattern('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&]).{8,}'), Validators.minLength(10)]),
      confirmPassword: this.fb.control<string|null>('', Validators.required),
    }, { validators: [Validation.match('password', 'confirmPassword')] });
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
  }

  refresh(always?:Function, next?: Function, error?: Function) {
    this.processing = true;
    this.dataService.getCurrentUser().subscribe({
      next: (userInfo: UserInfo) => {
        this.userInfo = new UserInfo(userInfo);
        this.processing = false;
        if(!_.isNil(next)){
          next();
        }
        if(!_.isNil(always)){
          always();
        }
      }, 
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
        if(!_.isNil(error)){
          error();
        }
        if(!_.isNil(always)){
          always();
        }
      }
    })
  }

  ngOnInit() {
    this.refresh();
  }

  cancelEditing(): void {
    if(this.processing) {
      return;
    }

    this.editing = false;
    this.editFormGroup.reset();
  }

  startEditing(): void {
    this.editFormGroup.patchValue(this.userInfo);
    this.editing = true;
  }

  editFormChanges(): any {
    let data: any = {};

    if(this.editFormGroup.value.email != this.userInfo.email) {
      data["email"] = this.editFormGroup.value.email;
    }

    if(this.editFormGroup.value.firstName != this.userInfo.firstName) {
      data["firstName"] = this.editFormGroup.value.firstName;
    }

    if(this.editFormGroup.value.lastName != this.userInfo.lastName) {
      data["lastName"] = this.editFormGroup.value.lastName;
    }

    if(this.editFormGroup.value.profilePic != this.userInfo.profilePic) {
      data["profilePic"] = this.editFormGroup.value.profilePic;
    }

    return data;
  }
  
  editFormHasChanges(): boolean {
    return !isNilOrEmpty(this.editFormChanges());
  }

  save(): void {
    if (this.editFormGroup.invalid) {
      return;
    }
    
    this.processing = true;
    
    this.dataService.updateUser(this.userInfo.id, this.editFormChanges()).subscribe({
      next: (data: UserInfo) => {
        this.userInfo = new UserInfo(data);
        this.processing = false;
        this.cancelEditing();
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  cancelChangePassword(): void {
    if(this.processing) {
      return;
    }

    this.changePassword = false;
    this.changePasswordFormGroup.reset();
  }

  startChangePassword(): void {
    this.changePassword = true;
  }

  savePassword(): void {
    if (this.changePasswordFormGroup.invalid) {
      return;
    }
    
    this.processing = true;
    this.dataService.updateUser(this.userInfo.id, {password: this.newPassword}).subscribe({
      next: (data: UserInfo) => {
        this.userInfo = new UserInfo(data);
        this.processing = false;
        this.cancelChangePassword();
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  disablePassword(): void {
    if(confirm("Are you sure you want to disable your password?  Doing so will prevent you from logging in with username and password.  You will need to log in via Google instead.")) {
      this.processing = true;
      this.dataService.updateUser(this.userInfo.id, {password: null}).subscribe({
        next: (data: UserInfo) => {
          this.userInfo = new UserInfo(data);
          this.editing = false;
          this.processing = false;
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
        }
      });
    }
  }

  _generateAPIKey(user: UserInfo): void {
    this.processing = true;
    this.dataService.generateUserAPIKey(user.id).subscribe({
      next: (resp: string) => {
        user.apiKey = resp;
        this.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    })
  }

  generateAPIKey(): void {
    let user = this.userInfo;
    if(!isNilOrEmpty(user.apiKey)) {
      if(confirm(`Are you sure you want to regenerate your API key?  The previous key will be invalidated.`)) {
        this._generateAPIKey(user);
      }
    } else {
      this._generateAPIKey(user);
    }
  }

  deleteAPIKey(): void {
    this.processing = true;
    if(confirm(`Are you sure you want to delete your API key?`)) {
      this.dataService.deleteUserAPIKey(this.userInfo.id).subscribe({
        next: (resp: string) => {
          this.userInfo.apiKey = "";
          this.processing = false;
        },
        error: (err: DataError) => {
          this.displayError(err.message);
          this.processing = false;
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

  get name(): string {
    if(_.isNil(this.userInfo)){
      return "UNKNOWN";
    }
    return `${this.userInfo.firstName} ${this.userInfo.lastName}`;
  }
}
