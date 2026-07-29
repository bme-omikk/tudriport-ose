import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtAuthorManagementComponent } from './ext-author-management.component';

describe('ExtAuthorManagementComponent', () => {
  let component: ExtAuthorManagementComponent;
  let fixture: ComponentFixture<ExtAuthorManagementComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExtAuthorManagementComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExtAuthorManagementComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
