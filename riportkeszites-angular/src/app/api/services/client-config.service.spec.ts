import { TestBed, inject } from '@angular/core/testing';

import { ClientConfigService } from './client-config.service';

describe('DashboardService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ClientConfigService]
    });
  });

  it('should be created', inject([ClientConfigService], (service: ClientConfigService) => {
    expect(service).toBeTruthy();
  }));
});
