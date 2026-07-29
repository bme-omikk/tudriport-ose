import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { InputQueueWaitingComponent } from './input-queue-waiting.component';

describe('InputQueueWaitingComponent', () => {
  let component: InputQueueWaitingComponent;
  let fixture: ComponentFixture<InputQueueWaitingComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ InputQueueWaitingComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(InputQueueWaitingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
