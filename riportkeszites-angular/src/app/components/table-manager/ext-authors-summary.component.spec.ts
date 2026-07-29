import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtAuthorsSummaryComponent } from './ext-authors-summary.component';

describe('ExtAuthorsSummaryComponent', () => {
  let component: ExtAuthorsSummaryComponent;
  let fixture: ComponentFixture<ExtAuthorsSummaryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExtAuthorsSummaryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExtAuthorsSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
