import * as _ from "lodash";

import { inject, Inject, Injectable, InjectionToken, EventEmitter } from '@angular/core';

import { Observable, throwError, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { HttpClient, HttpHeaders } from  '@angular/common/http';

import { WINDOW } from '../window.provider';
import { isNilOrEmpty } from '../utils/helpers';
import { Device, UserInfo } from '../models';

const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' })
};
export class DataError extends Error {
  statusCode!: number;
  statusText!: string;
  reason!: string;

  constructor(message?: string, statusCode?: any | undefined, statusText?: any | undefined, reason?: any | undefined){
    super(message);
    if (statusCode !== undefined){
      this.statusCode = statusCode;
    }
    if (statusText !== undefined) {
      this.statusText = statusText
    }
    if (reason !== undefined) {
      this.reason = reason;
    }
  }
}

//export const WINDOW = new InjectionToken('Window');

@Injectable({
  providedIn: 'root'
})
export class DataService {
  unauthorized: EventEmitter<DataError> 
  private http: HttpClient = inject(HttpClient);

  apiBaseUrl: string;
  baseUrl: string;

  constructor(@Inject(WINDOW) private window: Window) {
    this.unauthorized = new EventEmitter();

    const protocol = this.window.location.protocol
    const hostname = this.window.location.hostname;
    const port = this.window.location.port
    this.baseUrl = `${protocol}//${hostname}`;

    if (!((protocol === 'http:' && port === "80") || (protocol === 'https:' && port === "443"))){
      this.baseUrl = `${this.baseUrl}:${port}`;
    }

    this.apiBaseUrl = this.baseUrl + '/api/v1';
  }

  getError(error: any){
    let errObj = new DataError(error.error.message);
    if (!(error.error instanceof ErrorEvent)) {
      // handle server-side errors
      errObj.reason = error.message;
      errObj.statusCode = _.toInteger(error.status);
      errObj.statusText = error.statusText;

      if(errObj.statusCode === 401) {
        this.unauthorized.emit(errObj);
      }

      // This is a work around in case the browser got a 302 to redirect to the login page, but the original
      // request was not a GET so it tried to make an invalid request to /login instead of redirecting to the page
      if(errObj.statusCode === 405 && (!isNilOrEmpty(error.url) && _.startsWith(error.url, `${this.baseUrl}/login`))){
        window.location.href = error.url;
      }
    }
    return throwError(() => {return errObj});
  }

  getDevices(): Observable<Device[]> {
    const url: string = `${this.apiBaseUrl}/devices`;

    return this.http.get<Device[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getDevice(id: string): Observable<Device> {
    const url: string = `${this.apiBaseUrl}/devices/${id}`;

    return this.http.get<Device>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  updateDevice(id: string, data:any): Observable<Device> {
    const url: string = `${this.apiBaseUrl}/devices/${id}`;

    return this.http.patch<Device>(url, data, httpOptions).pipe(catchError((err) => {return this.getError(err)}));
  }

  createDevice(data:any): Observable<Device> {
    const url: string = `${this.apiBaseUrl}/devices`;

    return this.http.post<Device>(url, data, httpOptions).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteDevice(id: string): Observable<Device> {
    const url: string = `${this.apiBaseUrl}/devices/${id}`;

    return this.http.delete<Device>(url, httpOptions).pipe(catchError((err) => {return this.getError(err)}));
  }

  enableMaintenanceMode(id: string): Observable<Device> {
    return this.rpc(id, "start_maintenance_mode", {});
  }

  disableMaintenanceMode(id: string): Observable<Device> {
    return this.rpc(id, "stop_maintenance_mode", {});
  }

  enableCalibrationMode(id: string): Observable<Device> {
    return this.rpc(id, "start_calibration", {});
  }

  cancelCalibrationMode(id: string): Observable<Device> {
    return this.rpc(id, "cancel_calibration", {});
  }

  calibrate(id: string, calibrationWeight:number): Observable<Device> {
    return this.rpc(id, "calibrate", {calibrationWeight: calibrationWeight});
  }

  rpc(id: string, func:string, data:any): Observable<Device> {
    const url: string = `${this.apiBaseUrl}/devices/${id}/rpc/${func}`;
    return this.http.post<Device>(url, data, httpOptions).pipe(catchError((err) => {return this.getError(err)}));
  }

  login(email: string, password: string): Observable<any>{
    const url = `${this.apiBaseUrl}/auth/login`;
    return this.http.post<any>(url, {email, password}, httpOptions).pipe(catchError((err: any) => this.getError(err)));
  }

  getCurrentUser(): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/me`;
    return this.http.get<UserInfo>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getUsers(): Observable<UserInfo[]> {
    const url = `${this.apiBaseUrl}/users`;
    return this.http.get<UserInfo[]>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  getUser(id: String): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${id}`;
    return this.http.get<UserInfo>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  createUser(data: any): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users`;
    return this.http.post<UserInfo>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  updateUser(id: String, data: any): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${id}`;
    return this.http.patch<UserInfo>(url, data).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteUser(id: String): Observable<UserInfo> {
    const url = `${this.apiBaseUrl}/users/${id}`;
    return this.http.delete<UserInfo>(url).pipe(catchError((err) => {return this.getError(err)}));
  }

  generateUserAPIKey(userId: string): Observable<string> {
    const url = `${this.apiBaseUrl}/users/${userId}/api_key?regen=true`;
    return this.http.post<string>(url, {}).pipe(catchError((err) => {return this.getError(err)}));
  }

  deleteUserAPIKey(userId: string): Observable<any> {
    const url = `${this.apiBaseUrl}/users/${userId}/api_key`;
    return this.http.delete<any>(url, {}).pipe(catchError((err) => {return this.getError(err)}));
  }
}
