import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SubmitVrlJobComponent } from './submit-vrl-job.component';

describe('SubmitJobComponent', () => {
  let component: SubmitVrlJobComponent;
  let fixture: ComponentFixture<SubmitVrlJobComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SubmitVrlJobComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SubmitVrlJobComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
