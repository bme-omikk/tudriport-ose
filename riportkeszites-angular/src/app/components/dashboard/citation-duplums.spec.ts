import { CitationDuplumsComponent } from './citation-duplums.component';

import { async, ComponentFixture, TestBed } from '@angular/core/testing';


describe('CitationDuplumsComponent', () => {
  let component: CitationDuplumsComponent;
  let fixture: ComponentFixture<CitationDuplumsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CitationDuplumsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CitationDuplumsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
