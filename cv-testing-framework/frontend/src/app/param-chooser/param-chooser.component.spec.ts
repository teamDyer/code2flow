import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ParamChooserComponent } from './param-chooser.component';

describe('ParamChooserComponent', () => {
  let component: ParamChooserComponent;
  let fixture: ComponentFixture<ParamChooserComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ParamChooserComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ParamChooserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
