import { TestBed, inject } from '@angular/core/testing';

import { LanguageSwitchService } from './switch-language.service';

describe('LanguageSwitchService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [LanguageSwitchService]
    });
  });

  it('should be created', inject([LanguageSwitchService], (service: LanguageSwitchService) => {
    expect(service).toBeTruthy();
  }));
});
