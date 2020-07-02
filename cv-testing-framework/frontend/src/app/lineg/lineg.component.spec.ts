import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LinegComponent } from './lineg.component';

describe('LinegComponent', () => {
  let component: LinegComponent;
  let fixture: ComponentFixture<LinegComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LinegComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LinegComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
