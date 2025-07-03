import { Component, inject, model, signal } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { Device, DeviceState, UserInfo } from '../models';
import { FormGroup, FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { isNilOrEmpty, goto } from '../utils/helpers'
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
import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogActions,
  MatDialogContent,
  MatDialogRef,
  MatDialogTitle,
} from '@angular/material/dialog';

class DeviceExt extends Device {
  processing: boolean = false;
}

export interface CalibrateDeviceDialogData {
  device: Device;
}

@Component({
  selector: 'app-devices',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSelectModule, MatProgressSpinnerModule, MatTableModule, MatIconModule, MatMenuModule],
  templateUrl: './devices.component.html',
  styleUrl: './devices.component.scss'
})
export class DevicesComponent {
  private _snackBar = inject(MatSnackBar);
  readonly dialog = inject(MatDialog);
  DeviceState = DeviceState; // Make the enum available to the template

  loading = false;
  updating = false;
  editWeightScaleForm: FormGroup;
  editWeightScale = false;
  addWeightScale = false;
  editFlowMonitor = false;
  selectedDevice!: DeviceExt;
  me: UserInfo | null = null;

  allowedLiquidUnits = ["ml", "l", "gal"];
  allowedMassUnits = ["g", "oz", "lb"];

  devices: DeviceExt[] = [];

  adminDisplayColumns = ["status", "type", "name", "remaining", "measurements", "actions"]
  displayedColumns = ["status", "type", "name", "remaining", "measurements"]

  isMobile = false;

  constructor(private dataService: DataService, private fb: FormBuilder, private deviceService: DeviceDetectorService) { 
    this.editWeightScaleForm = this.fb.group({
      name: this.fb.control<string|null>('', Validators.required),
      emptyKegWeight: ['', Validators.required],
      emptyKegWeightUnit: ['', Validators.required],
      startVolume: ['', Validators.required],
      startVolumeUnit: ['', Validators.required],
      displayVolumeUnit: ['', Validators.required],
      chipType: this.fb.control<string|null>('', Validators.required),
      chipId: this.fb.control<string|null>('', Validators.required),
      deviceType: ['']
    });
    this.isMobile = deviceService.isMobile();
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
    this.dataService.getCurrentUser().subscribe({
      next: (me: UserInfo) => {
        if(isNilOrEmpty(me) || isNilOrEmpty(me.id)) {
          this.displayError("No user data returned for currently logged in user, redirecting to login screen");
          goto("login");
        } else {
          this.me = me;
          this.dataService.getDevices().subscribe({
            next: (devices: Device[]) => {
              this.devices = [];
              for(let i in devices) {
                this.devices.push(new DeviceExt(devices[i]));
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
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        if (err.statusCode === 401) {
          goto("login");
        } else {
          this.loading = false;
        }
      }
    });
  }

  addWeightScaleDevice(): void {
    this.selectedDevice = new DeviceExt();
    this.editWeightScaleForm.patchValue({chipType: "Particle", deviceType: "weight"});
    this.addWeightScale = true;
  }

  editDevice(dev: Device): void {
    this.loading =true;
    this.dataService.getDevice(dev.id).subscribe({
      next: (device: Device) => {
        this.selectedDevice = new DeviceExt(device);
        if (device.deviceType == "weight") {
          this.editWeightScale = true;
          this.editWeightScaleForm.patchValue(this.selectedDevice);
        } else {
          this.editFlowMonitor = true;

        }
        this.loading = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.loading = false;
      }
    })
  }

  editWeightScaleChanges(): any {
    let data: any = {};

    if(this.editWeightScaleForm.value.name != this.selectedDevice.name) {
      data["name"] = this.editWeightScaleForm.value.name;
    }

    if(this.editWeightScaleForm.value.chipType != this.selectedDevice.chipType) {
      data["chipType"] = this.editWeightScaleForm.value.chipType;
    }

    if(this.editWeightScaleForm.value.chipId != this.selectedDevice.chipId) {
      data["chipId"] = this.editWeightScaleForm.value.chipId;
    }

    if(this.editWeightScaleForm.value.emptyKegWeight != this.selectedDevice.emptyKegWeight) {
      data["emptyKegWeight"] = this.editWeightScaleForm.value.emptyKegWeight;
    }

    if(this.editWeightScaleForm.value.emptyKegWeightUnit != this.selectedDevice.emptyKegWeightUnit) {
      data["emptyKegWeightIUnit"] = this.editWeightScaleForm.value.emptyKegWeightUnit;
    }

    if(this.editWeightScaleForm.value.startVolume != this.selectedDevice.startVolume) {
      data["startVolume"] = this.editWeightScaleForm.value.startVolume;
    }

    if(this.editWeightScaleForm.value.startVolumeUnit != this.selectedDevice.startVolumeUnit) {
      data["startVolumeUnit"] = this.editWeightScaleForm.value.startVolumeUnit;
    }

    if(this.editWeightScaleForm.value.displayVolumeUnit != this.selectedDevice.displayVolumeUnit) {
      data["displayVolumeUnit"] = this.editWeightScaleForm.value.displayVolumeUnit;
    }

    return data;
  }

  editWeightScaleHasChanges(): boolean {
    return !isNilOrEmpty(this.editWeightScaleChanges());
  }

  onEditWeightScaleSubmit(): void {
    if (this.editWeightScaleForm.valid) {
      this.updating = true;
      if(this.addWeightScale) {
        this.dataService.createDevice(this.editWeightScaleForm.value).subscribe({
          next: (res: any) => {
            this.reload(undefined, () => {this.cancelEditWeightScale();});
            this.updating = false;
          },
          error: (err: DataError) => {
            this.displayError(err.message);
            this.updating = false;
          }
        });
      } else {
        let changes = this.editWeightScaleChanges();
        if (!isNilOrEmpty(changes)) {
          this.dataService.updateDevice(this.selectedDevice.id, changes).subscribe({
            next: (res: any) => {
              this.reload(undefined, () => {this.cancelEditWeightScale();});
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

  cancelEditWeightScale(): void {
    if(this.updating) {
      return;
    }
    this.editWeightScaleForm.reset();
    this.editWeightScale = false;
    this.addWeightScale = false;
    this.selectedDevice = new DeviceExt();
  }

  deleteDevice(dev: Device) {
    if(confirm(`Are you sure you want to delete device '${dev.name}'?`)) {
      this.dataService.deleteDevice(dev.id).subscribe({
        next: (res: any) => {
          this.reload();
        },
        error: (err: DataError) => {
          this.displayError(err.message);
        }
      });
    }
  }

  enableMaintenanceMode(d: DeviceExt): void {
    if(d.getState() != DeviceState.Ready && d.getState() != DeviceState.ReadyNoService) {
      return;
    }
    d.processing = true;
    this.dataService.enableMaintenanceMode(d.id).subscribe({
      next: (dev: Device) => {
        this.updateDeviceInList(dev);
        d.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        d.processing = false;
      }
    });
  } 

  disableMaintenanceMode(d: DeviceExt): void {
    if(d.getState() != DeviceState.MaintenanceModeEnabled) {
      return;
    }
    d.processing = true;
    this.dataService.disableMaintenanceMode(d.id).subscribe({
      next: (dev: Device) => {
        this.updateDeviceInList(dev);
        d.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        d.processing = false;
      }
    });
  }

  cancelCalibration(dev: DeviceExt) {
    if(dev.getState() != DeviceState.CalibrationModeEnabled) {
      return;
    }

    dev.processing = true;
    this.dataService.cancelCalibrationMode(dev.id).subscribe({
      next: (_dev: Device) => {
        this.updateDeviceInList(new Device(_dev));
        dev.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        dev.processing = false;
      }
    });
  }

  calibrate(dev: DeviceExt) {
    dev.processing = true;
    if(dev.deviceType == "weight") {
      this.openCalibrateWeightDialog(dev);
    }
  }

  updateDeviceInList(dev: Device): void {
    for(let i in this.devices) {
      let d = this.devices[i];
      if (d.id == dev.id) {
        this.devices[i].from(dev);
      }
    }
  }

  disableEnableMaintenanceButton(dev: Device): boolean {
    if (dev.online) {
      if (dev.getState() != DeviceState.MaintenanceModeEnabled && dev.getState() != DeviceState.Calibrating) {
        return false;
      }
    }
    return true;
  }

  showDisableMaintenanceButton(dev: Device): boolean {
    if (dev.online && dev.getState() == DeviceState.MaintenanceModeEnabled) {
      return true;
    }

    return false;
  }

  disableCalibrateButton(dev: Device): boolean {
    if (dev.online) {
      if (dev.getState() != DeviceState.Calibrating) {
        return false;
      }
    }

    return true;
  }

  showStopCalibrationButton(dev: Device): boolean {
    if (dev.getState() == DeviceState.Calibrating) {
      return false;
    }

    if (dev.online) {
      if (dev.getState() == DeviceState.CalibrationModeEnabled) {
        return true;
      }
    }
    
    return false;
  }

  openCalibrateWeightDialog(dev: DeviceExt): void {
    const dialogRef = this.dialog.open(CalibrateDeviceDialog, {
      data: {device: new Device(dev)},
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('The dialog was closed');
      if (result !== undefined) {
        this.updateDeviceInList(result);
        dev.processing = false;
      } else {
        this.dataService.getDevice(dev.id).subscribe({
          next: (_d: Device) => {
            this.updateDeviceInList(new Device(_d));
            dev.processing = false;
          },
          error: (err: DataError) => {
            this.displayError(err.message);
            dev.processing = false;
          }
        });
      }
    });
  }

  get isAdmin(): boolean {
    if (_.isNull(this.me) || isNilOrEmpty(this.me?.id)) {
      return false;
    }
    
    return this.me.admin;
  }
}

@Component({
  selector: 'calibrate-device-dialog',
  templateUrl: 'calibrate-device-dialog.html',
  imports: [
    MatFormFieldModule,
    MatInputModule,
    FormsModule,
    MatButtonModule,
    MatDialogTitle,
    MatDialogContent,
    MatDialogActions,
    MatProgressSpinnerModule,
  ],
})
export class CalibrateDeviceDialog {
  private _snackBar = inject(MatSnackBar);
  DeviceState = DeviceState; // Make the enum available to the template

  readonly dialogRef = inject(MatDialogRef<CalibrateDeviceDialog>);
  readonly data = inject<CalibrateDeviceDialogData>(MAT_DIALOG_DATA);
  
  device = this.data.device;
  calibrationValue: number;
  processing = false;

  constructor(private dataService: DataService, private fb: FormBuilder) { 
    this.calibrationValue = 0;

    this.dialogRef.afterOpened().subscribe(_ => {
      this.calibrationValue = 0;
      this.processing = false;
    });
  }

  cancel() {
    if(this.device.getState() != DeviceState.CalibrationModeEnabled) {
      return;
    }

    this.processing = true;
    this.dataService.cancelCalibrationMode(this.device.id).subscribe({
      next: (dev: Device) => {
        this.close(new Device(dev));
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  close(data?: any) {
    this.dialogRef.close(data);
  }

  enableCalibration() {
    if(this.device.getState() != DeviceState.Ready && this.device.getState() != DeviceState.ReadyNoService) {
      return;
    }

    this.processing = true;
    console.log("starting enable_calibration call")
    this.dataService.enableCalibrationMode(this.device.id).subscribe({
      next: (dev: Device) => {
        this.device = new Device(dev);
        console.log(this.device);
        this.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.processing = false;
      }
    });
  }

  calibrate() {
    if(this.device.getState() != DeviceState.CalibrationModeEnabled) {
      return;
    }

    this.processing = true;
    this.dataService.calibrate(this.device.id, this.calibrationValue).subscribe({
      next: (dev: Device) => {
        this.close(new Device(dev));
        this.processing = false;
      },
      error: (err: DataError) => {
        this.displayError(err.message);
        this.dataService.getDevice(this.device.id).subscribe({
          next: (dev: Device) => {
            this.device = new Device(dev);
            this.processing = false;
          },
          error: (err: DataError) => {
            this.displayError(err.message);
            this.processing = false;
          }
        })
      }
    });
  }

  disableCalibrationBtn(): boolean {
    if(this.calibrationValue > 0) {
      return false;
    }

    return true;
  }

  displayError(errMsg: string) {
    this._snackBar.open("Error: " + errMsg, "Close");
    console.log("Error: " + errMsg, "Close");
  }
}