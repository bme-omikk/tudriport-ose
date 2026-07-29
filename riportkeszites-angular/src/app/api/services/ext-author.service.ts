import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { catchError, map, tap } from 'rxjs/operators';

import { ApiConfiguration } from '../api.configuration';
import { ExtAuthor, ExtAuthorlist } from '../models/ext-author';

import { BaseService } from './base.service';
import { TableData } from '../models/table-data'
import { CitationDuplum } from '../models/citation-duplum';
import { ExtraField } from '../../api/models/extra-field';
import { Type, Typesubtype} from '../models/typesubtype'
import { Character } from '../models/character';
@Injectable({
  providedIn: 'root'
})
export class ExtAuthorService extends BaseService {
  createFromFile(data: ExtAuthor) {
    return this.postRaw<ExtAuthor>(this.config.extAuthorCreateFromFile, data);
  }

  getSummaryPoints(mode: string, org: String, unit: String, subunit: String, subsubunit: String, year: String, validityDate: String, extraParams) {
    var url = this.config.extAuthorsSummary.replace(/{mode}/, mode);
    if (org) {
      url += `${org}/`
      if (unit) {
        url += `${unit}/`
        if (subunit) {
          url += `${subunit}/`
          if (subsubunit) {
            url += `${subsubunit}/`
          }
        }
      }
    }

    let params = extraParams;
    if (year != undefined && year != "") {
      params['year'] = year;
    }
    if(validityDate != undefined && validityDate != ""){
      params['dbdatetime'] = validityDate;
    }
    return this.getRaw<TableData>(url, params);
  }

  getExtAuthorDetails(mode: string, mtmt: number, year: number, org: String, unit: String, subunit: String, subsubunit: String,validityDateISO: string, extraParams) {
    var url = this.config.extAuthorDetails.replace(/{mode}/, mode); 
    let params = extraParams;
    if(validityDateISO != undefined && validityDateISO != ""){
      params['dbdatetime'] = validityDateISO;
    }    
    if(mtmt){
      url += `${mtmt}/`
      if(year){
        url += `${year}/`
      }
    } 
    else if (org) {
      url += `${org}/`
      if (unit) {
        url += `${unit}/`
        if (subunit) {
          url += `${subunit}/`
          if (subsubunit) {
            url += `${subsubunit}/`
          }
        }
      }
      if(year){
        url += `${year}/`
      }
    }         
    return this.getRaw<TableData>(url, params);
  }

  getAdhocPoints(mode: string, mtmt: number, org: String, unit: String, subunit: String, subsubunit: String, yearFrom: number, yearTo:number, type: string, subtype: string, character: string, pubids: string, validityDateISO: string, extraParams){
    var url = this.config.extAuthorAdhoc.replace(/{mode}/, mode);
    let params = extraParams;
    if(mtmt){
      params['mtmt'] = mtmt;
    }
    if (org) {
      params['org'] = org;
      if (unit) {
        params['unit'] = unit;
        if (subunit) {
          params['subunit'] = subunit;
          if (subsubunit) {
            params['subsub_unit'] = subsubunit;
          }
        }
      }
    }
    if(yearFrom){
      params['year_from'] = yearFrom;
    }
    if(yearTo){
      params['year_to'] = yearTo;
    }
    if(type){
      params['type'] = type;
    }
    if(subtype){
      params['subtype'] = subtype;
    }
    if(character){
      params['character'] = character;
    }
    if(pubids && pubids != ""){
      params['pubids'] = pubids;
    }
    if(validityDateISO){
      params['dbdatetime'] = validityDateISO;
    }
    return this.getRaw<TableData>(url, params);
  }

  getModes() {
    return this.getRaw<string[]>(this.config.riportModes);
  }

  getOrganizations(dbdatetime: string) {
    if(dbdatetime != null){
      let params = {}; 
      params['dbdatetime'] = dbdatetime;
      return this.getRaw<string[]>(this.config.extAuthorOrganizations, params);
    }
    return this.getRaw<string[]>(this.config.extAuthorOrganizations);
  }

  getUnits(org: string, dbdatetime: string) {
    if(dbdatetime != null){
      let params = {}; 
      params['dbdatetime'] = dbdatetime;
      return this.getRaw<string[]>(this.config.extAuthorUnits.replace(/{org}/, org), params);
    }
    return this.getRaw<string[]>(this.config.extAuthorUnits.replace(/{org}/, org));
  }

  getSubUnits(org: string, unit: string, dbdatetime: string) {
    if(dbdatetime != null){
      let params = {}; 
      params['dbdatetime'] = dbdatetime;
      return this.getRaw<string[]>(this.config.extAuthorSubUnits.replace(/{org}/, org).replace(/{unit}/, unit), params);
    }
    return this.getRaw<string[]>(this.config.extAuthorSubUnits.replace(/{org}/, org).replace(/{unit}/, unit));
  }

  getSubSubUnits(org: string, unit: string, subunit: string, dbdatetime: string) {
    if(dbdatetime != null){
      let params = {}; 
      params['dbdatetime'] = dbdatetime;
      return this.getRaw<string[]>(this.config.extAuthorSubSubUnits.replace(/{org}/, org).replace(/{unit}/, unit).replace(/{subunit}/, subunit), params);
    }
    return this.getRaw<string[]>(this.config.extAuthorSubSubUnits.replace(/{org}/, org).replace(/{unit}/, unit).replace(/{subunit}/, subunit));
  }
  getAuthors(org: string, unit: string, subunit: string, subsubunit: string, dbdatetime: string){
    let params = {}; 
    if(dbdatetime != null){
      params['dbdatetime'] = dbdatetime;
    }
    if(subsubunit != null){
      return this.getRaw<ExtAuthorlist[]>(this.config.extAuthorlistAuthorsSubsubunit.replace(/{org}/, org).replace(/{unit}/, unit).replace(/{subunit}/, subunit).replace(/{subsubunit}/, subsubunit), params); 
    }
    if(subunit != null){
      return this.getRaw<ExtAuthorlist[]>(this.config.extAuthorlistAuthorsSubunit.replace(/{org}/, org).replace(/{unit}/, unit).replace(/{subunit}/, subunit), params);
    }
    if(unit != null){
      return this.getRaw<ExtAuthorlist[]>(this.config.extAuthorlistAuthorsUnit.replace(/{org}/, org).replace(/{unit}/, unit), params);
    }    
    if(org != null){
      return this.getRaw<ExtAuthorlist[]>(this.config.extAuthorlistAuthorsOrg.replace(/{org}/, org), params);        
    }
    return this.getRaw<ExtAuthorlist[]>(this.config.extAuthorlistAuthors, params);
  } 
  getCitationDuplums(dbdatetime: string) {
    if(dbdatetime != null){
      return this.getRaw<CitationDuplum[]>(this.config.citationDuplumsDbDatetime.replace(/{dbdatetime}/, dbdatetime));
    }    
    return this.getRaw<CitationDuplum[]>(this.config.citationDuplums);
  }
  getTypes(){
    return this.getRaw<Type[]>(this.config.Type);
  } 
  getTypesubtypes(type: string){
    if(type!=null){
      return this.getRaw<Typesubtype[]>(this.config.TypesubtypesType.replace(/{type}/, type));
    }
    return this.getRaw<Typesubtype[]>(this.config.Typesubtypes);
  }
  getCharacters(){
    return this.getRaw<Character[]>(this.config.Characters);
  }


  postExtAuthorlist(author: ExtAuthorlist) : Observable<ExtAuthorlist>{
    let data = {
      "org": author.org,
      "unit": author.unit,
      "subunit": author.subunit,
      "subsub_unit": author.subsub_unit,
      "personname": author.personname,
      "mtmtcode": author.mtmtcode,
      "role": author.role,
      "weighting": author.weighting,
      "neptuncode": author.neptuncode,
      "supervisor_mtmt_authid": author.supervisor_mtmt_authid,
      "for_rollup": author.for_rollup
    };
    return this.postRaw(this.config.manageExtAuthorlist, data);
  }
  putExtAuthorlist(author: ExtAuthorlist) : Observable<ExtAuthorlist>{
    let data = {
      "id": author.id,
      "org": author.org,
      "unit": author.unit,
      "subunit": author.subunit,
      "subsub_unit": author.subsub_unit,
      "personname": author.personname,
      "mtmtcode": author.mtmtcode,
      "role": author.role,
      "weighting": author.weighting,
      "neptuncode": author.neptuncode,
      "supervisor_mtmt_authid": author.supervisor_mtmt_authid,
      "for_rollup": author.for_rollup
    };
    return this.postRaw(this.config.manageExtAuthorlist, data);
  }
  deleteExtAuthorlist(author: ExtAuthorlist){
    return this.deleteRaw(this.config.deleteExtAuthorlist.replace(/{id}/, author.id))
  }
  getExtraFileds(mode: string){
    return this.getRaw<ExtraField[]>(this.config.riportExtraFields.replace(/{mode}/, mode))
  }
}
