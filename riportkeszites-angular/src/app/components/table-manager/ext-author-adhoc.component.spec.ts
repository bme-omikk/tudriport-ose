// Angular Imports
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtAuthorAdhocComponent } from './ext-author-adhoc.component';

describe('ExtAuthorAdhocComponent', () => {
  let component: ExtAuthorAdhocComponent;
  let fixture: ComponentFixture<ExtAuthorAdhocComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExtAuthorAdhocComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExtAuthorAdhocComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});