import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DenseTableCellComponent } from './dense-table-cell.component';

describe('DenseTableCellComponent', () => {
  let component: DenseTableCellComponent;
  let fixture: ComponentFixture<DenseTableCellComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DenseTableCellComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DenseTableCellComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
