import { Component, OnInit, Output, Input, EventEmitter } from '@angular/core';
import { validateHorizontalPosition } from '@angular/cdk/overlay';

// Describes a user provided parameter. There is a simple type system for constraining
// what a user can provide. See backend/src/visualize.py for how the backend uses these parameters.
export interface ParameterDescription {
  name: string,
  type: 'query' | 'nat' | 'integer' | 'integer_range' | 'real' | 'real_range' | 'text' | 'string' | 'boolean' | 'date' | 'some' | 'choice',
  options?: Array<string>;
  optional: boolean;
  min?: number;
  max?: number;
  default?: any;
  doc?: string;
  no_duplicates?: boolean;
  depends?: Array<string>;
}

/* Mutate model so that it conforms to the parameter descriptions. */
export function makeModelConform(descriptions: Array<ParameterDescription>, modelObj: object, checkValid = false): boolean {
  let modified = false;
  let completelyValid = true;
  for (let param of descriptions) {
    let name = param.name;
    let model = modelObj[name];
    let oldmodel = model;
    let valid = false;
    switch (param.type) {
      default:
        valid = true;
        break;
      case 'boolean':
        model = model == 'true' ? true : model == 'false' ? false : model;
        valid = model === true || model === false;
        break;
      case 'query':
        valid = param.options.indexOf(model) != -1;
        break;
      case 'nat':
        model = Number(model);
        valid = Number.isInteger(model) && model >= 0;
        break;
      case 'integer':
        model = Number(model);
        valid = Number.isInteger(model);
        break;
      case 'integer_range':
        model = Number(model);
        valid = Number.isInteger(model) && model >= param.min && model <= param.max;
        break;
      case 'real':
        model = Number(model);
        valid = typeof (model) === 'number';
        break;
      case 'real_range':
        model = Number(model);
        valid = typeof (model) === 'number' && model >= param.min && model <= param.max;
        break;
      case 'text':
      case 'string':
        // Allow empty string only if param is optional.
        valid = typeof (model) === 'string' && !(!param.optional && model == '');
        break;
      case 'date':
        try {
          let trydate = new Date(model);
          valid = !!trydate.getMonth;
        } catch (err) {
          valid = false;
        }
        break;
      case 'some':
        valid = Array.isArray(model);
        if (param.no_duplicates && valid) {
          valid = model.length === new Set(model).size;
        }
        break;
    }
    if (valid) {
      if (oldmodel !== model) {
        modified = true;
      }
      modelObj[name] = model;
    } else {
      completelyValid = false;
      modified = true;
      delete modelObj[name];
      if (param.default != null) {
        let d = param.default;
        if (param.type === 'date') {
          d = new Date(d);
        }
        modelObj[name] = d;
      }
      if (param.type === 'some') {
        modelObj[name] = [];
      }
    }
  }
  if (checkValid) {
    return completelyValid;
  }
  return modified;
}

@Component({
  selector: 'app-param-chooser',
  templateUrl: './param-chooser.component.html',
  styleUrls: ['./param-chooser.component.css']
})
export class ParamChooserComponent implements OnInit {

  parameterDescriptions: Array<ParameterDescription> = [];

  // model for temporary stuff
  transientModel: object = {};

  @Input() model: object = {};
  @Output() modelChange = new EventEmitter<object>();

  @Input() set params(value: Array<ParameterDescription>) {
    this.parameterDescriptions = value;
    makeModelConform(value, this.model);
  }

  refresh() {
    this.modelChange.emit(this.model);
  }

  trackByFn(index: number, item: ParameterDescription) {
    return JSON.stringify(item);
  }

  addValuesToMulti(model, name, values, noDups) {
    if (values) {
      for (let v of values) {
        // prevent duplicates if no_duplicates is true
        if (noDups && model[name].indexOf(v) !== -1) {
          continue;
        }
        model[name].push(v);
      }
    }
  }

  removeValueFromMulti(model, name, index) {
    model[name].splice(index, 1);
  }

  constructor() { }

  ngOnInit() {
  }

}
