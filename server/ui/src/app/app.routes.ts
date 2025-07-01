import { DevicesComponent } from './devices/devices.component';
import { LoginComponent } from './login/login.component';
import { ProfileComponent } from './profile/profile.component'
import { UsersComponent } from './users/users.component'
import { Routes } from '@angular/router';

export const routes: Routes = [
    { path: 'home', component: DevicesComponent},
    { path: 'login', component:  LoginComponent, data: { hideHeader: true }},
    { path: 'me', component:  ProfileComponent},
    { path: 'users', component:  UsersComponent},
];
