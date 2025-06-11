import { DevicesComponent } from './devices/devices.component';
import { LoginComponent } from './login/login.component';
import { Routes } from '@angular/router';

export const routes: Routes = [
    { path: 'home', component: DevicesComponent },
    { path: 'login', component:  LoginComponent},
];
