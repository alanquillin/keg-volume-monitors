import { Component, inject, model, signal } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { Device, DeviceState } from '../models';
import { FormGroup, FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { isNilOrEmpty } from '../utils/helpers'
import * as _ from "lodash";
import { DeviceDetectorService } from 'ngx-device-detector';


import {MatButtonModule} from '@angular/material/button';
import {MatSelectModule} from '@angular/material/select';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatTableModule} from '@angular/material/table';
import {MatIconModule} from '@angular/material/icon';
import {MatMenuModule} from '@angular/material/menu';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatSnackBar} from '@angular/material/snack-bar';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSelectModule, MatProgressSpinnerModule, MatTableModule, MatIconModule, MatMenuModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  private _snackBar = inject(MatSnackBar);

  loginForm: FormGroup;
  processing = false;

  constructor(private dataService: DataService, private fb: FormBuilder, private deviceService: DeviceDetectorService) { 
    this.loginForm = this.fb.group({
      username: this.fb.control<string|null>('', Validators.required),
      password: this.fb.control<string|null>('', Validators.required),
      // Add more form controls as needed
    });
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
    console.log("Error: " + errMsg, "Close");
  }

  login(){
    this.processing = true;
    this.dataService.login(this.loginForm.value.username, this.loginForm.value.password).subscribe({
      next: (_: any) => {
        window.location.href = "/";
      },
      error: (err: DataError) => {
        if (err.statusCode === 400) {
          this.displayError(err.message)
        } else if (err.statusCode === 401) {
          this.displayError("Invalid username or password")
        } else {
          this.displayError("An unknown error occurred trying to login.")
        }
        this.processing = false;
      }
    });
  }
}
