import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExportcsvComponent } from './exportcsv.component';

describe('ExportcsvComponent', () => {
  let component: ExportcsvComponent;
  let fixture: ComponentFixture<ExportcsvComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExportcsvComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExportcsvComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
