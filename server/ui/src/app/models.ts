// since these will often be python API driven snake_case names
/* eslint-disable @typescript-eslint/naming-convention */
// this check reports that some of these types shadow their own definitions
/* eslint-disable no-shadow */

import * as _ from 'lodash';

export class Device {
  id!: string;
  name!: string;
  chipType!: string;
  chipId!: string;
  chipModel!: string;
  offset!: number;
  offsetUnit!: string;
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
}