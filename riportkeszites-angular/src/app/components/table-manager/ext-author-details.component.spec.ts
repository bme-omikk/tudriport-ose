import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtAuthorDetailsComponent } from './ext-author-details.component';

describe('ExtAuthorDetailsComponent', () => {
  let component: ExtAuthorDetailsComponent;
  let fixture: ComponentFixture<ExtAuthorDetailsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExtAuthorDetailsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExtAuthorDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
