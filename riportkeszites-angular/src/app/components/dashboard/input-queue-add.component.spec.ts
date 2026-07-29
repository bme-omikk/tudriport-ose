import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { InputQueueAddComponent } from './input-queue-add.component';

describe('InputQueueAddComponent', () => {
  let component: InputQueueAddComponent;
  let fixture: ComponentFixture<InputQueueAddComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ InputQueueAddComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(InputQueueAddComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
