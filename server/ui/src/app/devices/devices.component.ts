import { Component } from '@angular/core';
import { DataService, DataError } from '../_services/data.service';
import { Device } from '../models';
import { FormGroup, FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { isNilOrEmpty } from '../utils/helpers'
import * as _ from "lodash";

@Component({
  selector: 'app-devices',
  imports: [ReactiveFormsModule],
  templateUrl: './devices.component.html',
  styleUrl: './devices.component.scss'
})
export class DevicesComponent {
  loading = false;
  updating = false;
  editWeightScaleForm: FormGroup;
  editWeightScale = false;
  editFlowMonitor = false;
  selectedDevice!: Device;

  allowedLiquidUnits = ["ml", "l", "gal"];
  allowedMassUnits = ["g", "oz", "lb"];

  devices: Device[] = [];

  constructor(private dataService: DataService, private fb: FormBuilder) { 
    this.editWeightScaleForm = this.fb.group({
      name: this.fb.control<string|null>('', Validators.required),
      emptyKegWeight: ['', Validators.required],
      emptyKegWeightUnit: ['', Validators.required],
      startVolume: ['', Validators.required],
      startVolumeUnit: ['', Validators.required],
      displayVolumeUnit: ['', Validators.required]
      // Add more form controls as needed
    });
  }

  displayError(errMsg: string) {
    //this._snackBar.open("Error: " + errMsg, "Close");
    console.log("Error: " + errMsg, "Close");
  }

  ngOnInit(): void {
    this.reload();
  }

  reload(always?:Function, next?: Function, error?: Function) {
    this.loading = true;
    this.dataService.getDevices().subscribe({
      next: (devices: Device[]) => {
        this.devices = devices;
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

  editDevice(dev: Device): void {
    this.loading =true;
    this.dataService.getDevice(dev.id).subscribe({
      next: (device: Device) => {
        this.selectedDevice = device;
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
    let changes = this.editWeightScaleChanges();
    if (this.editWeightScaleForm.valid && !isNilOrEmpty(changes)) {
      this.updating = true;
      console.log(changes);
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

  cancelEditWeightScale(): void {
    if(this.updating) {
      return;
    }
    this.editWeightScaleForm.reset();
    this.editWeightScale = false;
    this.selectedDevice = new Device();
  }
}
