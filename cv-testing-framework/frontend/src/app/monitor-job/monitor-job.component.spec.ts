import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MonitorJobComponent } from './monitor-job.component';

describe('MonitorJobComponent', () => {
  let component: MonitorJobComponent;
  let fixture: ComponentFixture<MonitorJobComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MonitorJobComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MonitorJobComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
