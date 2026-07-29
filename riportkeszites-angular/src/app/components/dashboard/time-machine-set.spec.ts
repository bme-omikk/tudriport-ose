// This Module's Components
import { TimeMachineSetComponent } from './time-machine-set.component';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

describe('TimeMachineSetComponent', () => {
  let component: TimeMachineSetComponent;
  let fixture: ComponentFixture<TimeMachineSetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TimeMachineSetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TimeMachineSetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});