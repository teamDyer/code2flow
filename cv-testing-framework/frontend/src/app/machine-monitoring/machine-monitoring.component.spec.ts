import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MachineMonitoringComponent } from './machine-monitoring.component';

describe('MachineMonitoringComponent', () => {
  let component: MachineMonitoringComponent;
  let fixture: ComponentFixture<MachineMonitoringComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MachineMonitoringComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MachineMonitoringComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
