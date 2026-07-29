import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtAuthorImportComponent } from './ext-author-import.component';

describe('ExtAuthorImportComponent', () => {
  let component: ExtAuthorImportComponent;
  let fixture: ComponentFixture<ExtAuthorImportComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExtAuthorImportComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExtAuthorImportComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
