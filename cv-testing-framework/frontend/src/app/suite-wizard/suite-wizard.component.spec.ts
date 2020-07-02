import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SuiteWizardComponent } from './suite-wizard.component';

describe('SuiteWizardComponent', () => {
  let component: SuiteWizardComponent;
  let fixture: ComponentFixture<SuiteWizardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SuiteWizardComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SuiteWizardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
