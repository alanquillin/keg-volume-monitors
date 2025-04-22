import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';

import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { HttpClient } from '@angular/common/http';

import { WINDOW_PROVIDERS } from './window.provider';

@NgModule({
  declarations: [],
  imports: [
    BrowserAnimationsModule,
    BrowserModule,
    FormsModule,
    //FooterComponent,
    ReactiveFormsModule,
  ],
  providers: [HttpClient, WINDOW_PROVIDERS],
  bootstrap: []
})
export class AppModule { }
