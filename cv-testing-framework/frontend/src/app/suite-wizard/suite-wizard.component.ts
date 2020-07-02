import { Component, OnInit } from '@angular/core';
import { ParameterDescription } from '../param-chooser/param-chooser.component';

@Component({
  selector: 'app-suite-wizard',
  templateUrl: './suite-wizard.component.html',
  styleUrls: ['./suite-wizard.component.css']
})
export class SuiteWizardComponent implements OnInit {

  wizardModel: object = {};
  wizardError?: string = null;
  wizardParams: ParameterDescription[] = [{
    name: 'columns',
    type: 'some',
    options: ['machine_id_config', 'gpu_id', 'branch_id', 'p4cl_id', 'user_id', 'subtest_set_id'],
    optional: false,
    no_duplicates: true,
    doc: "Simple description for bob"
  }];

  constructor() { }

  ngOnInit() {
  }

  refresh() {

  }

}
