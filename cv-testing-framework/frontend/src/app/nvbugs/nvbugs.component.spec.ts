import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NvbugsComponent } from './nvbugs.component';

describe('NvbugsComponent', () => {
  let component: NvbugsComponent;
  let fixture: ComponentFixture<NvbugsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ NvbugsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NvbugsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
