import { DevicesComponent } from './devices/devices.component';
import { ErrorsComponent } from './errors/errors.component'
import { LoginComponent } from './login/login.component';
import { ProfileComponent } from './profile/profile.component'
import { UsersComponent } from './users/users.component'
import { SettingsComponent } from './settings/settings.component'
import { Routes } from '@angular/router';

export const routes: Routes = [
    { path: 'home', component: DevicesComponent},
    { path: 'login', component:  LoginComponent, data: { hideHeader: true, access: { restricted: false }}},
    { path: 'me', component:  ProfileComponent},
    { path: 'users', component:  UsersComponent},
    { path: 'settings', component:  SettingsComponent},
    { path: 'unauthorized', component: ErrorsComponent, data: { error: "unauthorized", access: { restricted: false }} },
    { path: 'forbidden', component: ErrorsComponent, data: { error: "forbidden", access: { restricted: false }} },
    { path: 'error', component: ErrorsComponent, data: { error: "unknown",access: { restricted: false }} },
    { path: 'not-found', component: ErrorsComponent, data: { error: "notFound", access: { restricted: false }} },
    { path: '404', component: ErrorsComponent, data: { error: "notFound", access: { restricted: false }} },
    { path: 'login', component:  LoginComponent, data: { hideHeader: true, access: { restricted: false }}},
    { path: '**', redirectTo: '/404' }
];
