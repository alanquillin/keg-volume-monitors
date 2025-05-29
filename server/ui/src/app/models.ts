// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */
// this check reports that some of these types shadow their own definitions
/* eslint-disable no-shadow */

import * as _ from 'lodash';
import { isNilOrEmpty } from './utils/helpers';

export enum DeviceState {
  Ready, ReadyNoService, CalibrationModeEnabled, Calibrating, MaintenanceModeEnabled, Unknown
}

export class Device {
  id!: string;
  name!: string;
  chipType!: string;
  chipId!: string;
  chipModel!: string;
  measurementCount!: number;
  latestMeasurement!: number;
  latestMeasurementUnit!: string;
  latestMeasurementTakenOn!: string;
  percentRemaining!: number;
  totalVolumeRemaining!: number;
  deviceType!: string;
  emptyKegWeight!: number;
  emptyKegWeightUnit!: string;
  startVolume!: number;
  startVolumeUnit!: string;
  displayVolumeUnit!: string;
  online!: boolean;
  state!: number;
  stateStr!: string;

  constructor(from?: any) {
    if(!isNilOrEmpty(from)) {
      this.from(from);
    }
  }

  from(from: any): void {
    Object.assign(this, from);
  }

  getState(): DeviceState {
    if (this.state == 1) {
      return DeviceState.Ready;
    }
    if (this.state == 2) {
      return DeviceState.ReadyNoService;
    }
    if (this.state == 10) {
      return DeviceState.CalibrationModeEnabled;
    }
    if (this.state == 11) {
      return DeviceState.Calibrating;
    }
    if (this.state == 99) {
      return DeviceState.MaintenanceModeEnabled;
    }

    return DeviceState.Unknown;
  }
}