import { AbstractControl, ValidatorFn, ValidationErrors } from '@angular/forms';

import * as _ from 'lodash';
    
export class Validation {
    static match(controlName: string, checkControlName: string): ValidatorFn {
        return (controls: AbstractControl) : ValidationErrors | null => {
            const control = controls.get(controlName);
            const checkControl = controls.get(checkControlName);
            
            if (control && checkControl && control.value !== checkControl.value) {
                return { matching: true };
            }
            return null;
        };
    }
}