import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DvsUnitComponent } from './dvs-unit.component';

describe('DvsUnitComponent', () => {
  let component: DvsUnitComponent;
  let fixture: ComponentFixture<DvsUnitComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DvsUnitComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DvsUnitComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
