import { Component, OnInit, Input } from '@angular/core';
import { FormGroup } from '@angular/forms';
@Component({
  selector: 'app-unit-under-test',
  templateUrl: './unit-under-test.component.html',
  styleUrls: ['./unit-under-test.component.css']
})

/**
 * This component will work as a single point entry for different units integrated with CHub
 * 
 */

export class UnitUnderTestComponent implements OnInit {
  @Input() unit: string;
  @Input() parentForm: FormGroup
  constructor() { }

  ngOnInit() {
  }

}
