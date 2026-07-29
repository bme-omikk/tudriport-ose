import { TestBed, inject } from '@angular/core/testing';

import { ExtAuthorService } from './ext-author.service';

describe('ExtAuthorService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ExtAuthorService]
    });
  });

  it('should be created', inject([ExtAuthorService], (service: ExtAuthorService) => {
    expect(service).toBeTruthy();
  }));
});
