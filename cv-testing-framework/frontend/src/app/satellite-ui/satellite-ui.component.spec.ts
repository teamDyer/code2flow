import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SatelliteUiComponent } from './satellite-ui.component';

describe('satelliteUiComponent', () => {
  let component: SatelliteUiComponent;
  let fixture: ComponentFixture<SatelliteUiComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SatelliteUiComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SatelliteUiComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
