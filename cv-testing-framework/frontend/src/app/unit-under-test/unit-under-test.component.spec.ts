import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { UnitUnderTestComponent } from './unit-under-test.component';

describe('UnitUnderTestComponent', () => {
  let component: UnitUnderTestComponent;
  let fixture: ComponentFixture<UnitUnderTestComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ UnitUnderTestComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UnitUnderTestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
