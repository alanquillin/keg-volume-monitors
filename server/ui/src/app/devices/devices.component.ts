import { Component } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { Device } from '../models';

@Component({
  selector: 'app-devices',
  imports: [],
  templateUrl: './devices.component.html',
  styleUrl: './devices.component.scss'
})
export class DevicesComponent {
  loading = false;
  devices: Device[] = [];

  constructor(private dataService: DataService) { }

  displayError(errMsg: string) {
    //this._snackBar.open("Error: " + errMsg, "Close");
    console.log("Error: " + errMsg, "Close");
  }

  ngOnInit(): void {
    this.loading = true;
    this.dataService.getDevices().subscribe({
      next: (devices: Device[]) => {
        this.devices = devices;
        this.loading = false;
      },
      error: (err: DataError) => {
        if(err.statusCode !== 401) {
          this.displayError(err.message);
          this.loading = false;
        }
      }
    });
  }
}
