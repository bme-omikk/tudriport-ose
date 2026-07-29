import { TestBed, inject } from '@angular/core/testing';

import { InputQueueService } from './input-queue.service';

describe('InputQueueService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [InputQueueService]
    });
  });

  it('should be created', inject([InputQueueService], (service: InputQueueService) => {
    expect(service).toBeTruthy();
  }));
});
