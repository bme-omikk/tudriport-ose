import { NgModule, Injectable } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import {
  HttpClientModule,
  HttpXsrfTokenExtractor,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpClientXsrfModule,
  HTTP_INTERCEPTORS
} from '@angular/common/http';

import { ApiConfiguration } from './api.configuration'

@Injectable()
export class HttpXsrfInterceptor implements HttpInterceptor {
    constructor(private tokenExtractor: HttpXsrfTokenExtractor) {}

    intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
      const headerName = 'X-CSRFToken';
      let token = this.tokenExtractor.getToken() as string;
      if (token !== null && !req.headers.has(headerName)) {
          req = req.clone({ headers: req.headers.set(headerName, token) });
      }
      return next.handle(req);
    }
}

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    HttpClientXsrfModule.withOptions({
      cookieName: 'csrftoken',
      headerName: 'X-CSRFToken'
    })
  ],
  declarations: [],
  providers: [
    ApiConfiguration,
    { provide: HTTP_INTERCEPTORS, useClass: HttpXsrfInterceptor, multi: true }
  ],
  exports: [HttpClientModule],
})
export class ApiModule { }
