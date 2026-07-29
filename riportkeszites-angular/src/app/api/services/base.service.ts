import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { of, Observable, throwError } from 'rxjs';
import { catchError, map, tap, flatMap } from 'rxjs/operators';

import { ApiConfiguration } from '../api.configuration';
import { NotificationManager, NotificationType } from '../../notification-manager'
import { TranslateService } from '@ngx-translate/core';
const httpOptions = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json','Accept': 'application/json' }),
  withCredentials: true
};

@Injectable()
export abstract class BaseService {
  constructor(
      protected http: HttpClient,
      protected config: ApiConfiguration,
      protected notificationManager: NotificationManager,
      private translate: TranslateService
    ) { }

  private getErrorMessage(error: HttpErrorResponse): string {
      switch (error.status) {
        case 403:
          return 'Nincs jogosultsága a kért tartalomhoz! / You don\'t have permission.';
        case 404:
          return 'A kért tartalom nem található! / Requested content not found.';
        case 302:
          return 'Kérjük, töltse újra az oldalt és jelentkezzen be újra! Ha ismét ezt a hibát látja, kérjük, értesítse az üzemeltetőket. / Please reload.';
      }
      return 'Hiba a szerverrel való kommunikáció során. Ha ez a hiba először jelentkezik, kérjük, töltse újra az oldalt. / Unexpected error encountered. If you see this for the first time, please reload.';
  }

  private handleError<T>() {
    return (error: HttpErrorResponse): Observable<T> => {
      if (error.status == 400 && error.error) {
        return of(error.error as T);
      }
      this.notificationManager.add(this.getErrorMessage(error), NotificationType.error, 0);
      return throwError(error);
    }
  }

  private handleSuccess() {
      return (value, index) => {
          return of(value);
      };
  }

  protected getGeneralPipe<T>(httpMethod: Observable<T>): Observable<T> {
    return httpMethod.pipe(flatMap(this.handleSuccess()), catchError(this.handleError()));
  }

  protected postRaw<T>(url: string, data: any = {}) {
    return this.getGeneralPipe<T>(this.http.post<T>(url, data, httpOptions));
  }
  protected deleteRaw<T>(url: string){
    return this.getGeneralPipe<T>(this.http.delete<T>(url, httpOptions));
  }
  protected getRaw<T>(url: string, parameters?: any) {
    let options = httpOptions
    if (parameters) {      
      options['params'] = parameters;
    } else {
      options['params'] = {};
    }
    options['params']['language_code'] = this.translate.currentLang;
    
    return this.getGeneralPipe<T>(this.http.get<T>(url, options));
  }
}