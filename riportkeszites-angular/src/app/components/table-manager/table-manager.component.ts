import { Component, OnInit, ViewChild, Output, EventEmitter } from '@angular/core';
import { Injectable, ElementRef } from '@angular/core';
import { Observable } from 'rxjs';
import { ClientConfig } from 'src/app/api/models/client-config';
import { ClientConfigService } from 'src/app/api/services/client-config.service';

import * as XLSX from 'xlsx';

import { TableData } from '../../api/models/table-data'
import { BaseService } from '../../api/services/base.service'
import { NotificationManager, NotificationType } from '../../notification-manager'
import { GlobalsSharedSerevice } from 'src/app/app.component';
@Component({
  selector: 'app-table-manager',
  templateUrl: './table-manager.component.html',
  styleUrls: ['./table-manager.component.css']
})
export class TableManagerComponent implements OnInit {
  @ViewChild('tableContainer', { static: true }) container;
  @Output() openPopup: EventEmitter<any> = new EventEmitter();
  @Output() isDataLoaded: EventEmitter<boolean> = new EventEmitter();
  showLoadingBar: boolean;

  sortableTableClass = 'tudriport-sortable';
  exportableTableID = 'tudriport-list-table';
  exportableTablePresent: boolean = false;

  private clientConfig: ClientConfig;
  constructor(private notificationManager: NotificationManager,
              private clientConfigService: ClientConfigService,
              public globals: GlobalsSharedSerevice) { }

  ngOnInit() {
    this.clientConfigService.getData().subscribe(cc => this.clientConfig = cc);

    this.globals.setSearchFormVisibility(true);
    this.globals.setTableHasContent(false);

    // init DataTables to use locale aware sorting based on the browser's default locale
    // source: https://datatables.net/blog/2017-02-28
    if ( window.Intl ) {
      var collator = new window.Intl.Collator();
      var types = $.fn.dataTable.ext.type;

      delete types.order['string-pre'];
      types.order['string-asc'] = collator.compare;
      types.order['string-desc'] = function ( a, b ) {
          return collator.compare( a, b ) * -1;
      };
    }
  }

  refreshData(obs: Observable<TableData>) {
    this.isDataLoaded.emit(false);
    this.showLoadingBar = true;
    this.exportableTablePresent = false;
    this.container.nativeElement.innerHTML = "";
    obs.subscribe(data => {this.container.nativeElement.innerHTML = data.htmlData;
                           this.removeClickables();
                           this.addHandlers();
                           this.gpkPhDScript();
                           this.showLoadingBar = false;
                           this.exportableTablePresent = (document.getElementById(this.exportableTableID) != null);

                           if (document.getElementById(this.exportableTableID) != null) {
                            $('#'+this.exportableTableID+"."+this.sortableTableClass).DataTable({
                              // disable advanced DAtaTAbles features, as DAtaTables might be superseded by angular sortable tables
                              "paging": false,
                              "searching": false,
                              "info": false,
                              // use first row of thead to control ordering
                              "orderCellsTop": true,
                              // retain source ordering by default
                              "order": []
                            });
                           }

                           this.globals.setTableHasContent(true);
                           this.isDataLoaded.emit(true)
    });
  }

  addClickHandler(selector: string, handler) {
    let selected: NodeList = this.container.nativeElement.querySelectorAll(selector);
    for (var i = 0; i < selected.length; i++) {
        selected[i].addEventListener('click', handler.bind(this));
    }
  }

  addHandlers() {
    this.addClickHandler(".openpubids", this.openPubidsHandler);
    this.addClickHandler(".openciteids", this.openCiteidsHandler);
    this.addClickHandler(".openPopup", this.openPopupHandler);
    this.addClickHandler('.highlightable', this.addHighlightHandler);
    this.addClickHandler('.toggle-button', this.toggleVisibility);
    this.addClickHandler('.megjegyzesbutton', this.copymegjegyzesGpkPhd);
    this.addClickHandler('.urlbutton', this.generateUrlGpkPhd);
  }

  openPubidsHandler(event) {
    let pubIds: string = event.currentTarget.getAttribute('data-pubids');
    if (!pubIds) {
      this.notificationManager.add("Nincsenek megjeleníthető publikációk.", NotificationType.warning);
      return;
    }
    window.open(this.clientConfig.config.mtmt2.publication_list_view_url.replace("@@@", this.formatIds(pubIds)));
  }

  openCiteidsHandler(event) {
    let citeIds:string = event.currentTarget.getAttribute('data-citeids');
    if (!citeIds) {
      this.notificationManager.add("Nincsenek megjeleníthető hivatkozások.", NotificationType.warning);
      return;
    }
    window.open(this.clientConfig.config.mtmt2.citation_list_view_url.replace("@@@", this.formatIds(citeIds)));
  }

  openPopupHandler(event) {
    this.openPopup.emit(event);
  }
  removeClickables(){
    let selected: NodeList = this.container.nativeElement.querySelectorAll('.clickable');
    for (var i = 0; i < selected.length; i++) {
        let pubIds: string = (selected[i] as Element).getAttribute('data-pubids');
        let citeds: string = (selected[i] as Element).getAttribute('data-citeids');
        if (pubIds && this.formatIds(pubIds).length <= 0) {
          (selected[i] as Element).classList.remove('clickable', 'openPopup', 'openpubids');
        }
        if (citeds && this.formatIds(citeds).length <= 0) {
            (selected[i] as Element).classList.remove('clickable', 'openciteids');
        }
    }
  }
  formatIds(ids:string) : string{
    return ids.trim().replace(/\s/g,'').replace('[', '').replace(']', '').replace('%', '');
  }

  //GPK PHD pubtype_container_id alapján cserél megjelenítést
  gpkPhDScript(){
    function firstCharHungarian(text){
      let textLow = text.toLowerCase();
      if (textLow.startsWith('dzs')) {
        return text.substring(0,3);
      } else if (textLow.startsWith('cs') || textLow.startsWith('dz') || textLow.startsWith('gy') || textLow.startsWith('ly') || textLow.startsWith('ny') || textLow.startsWith('sz') || textLow.startsWith('ty') || textLow.startsWith('zs')) {
        return text.substring(0, 2);
      } else {
        return text.substring(0,1);
      }
    }
    function nameAbbreviation(text){
      let nameParts = text.split(/[, ]+/, 2);
      if (nameParts.length < 2) {
        return text;
      } else {
        return `${nameParts[0]} ${firstCharHungarian(nameParts[1])}.`;
      }
    }

    // egyedi URL generáló event handling
    const allapotok = document.querySelectorAll('input[id^="idl"], label[for^="idl"]');
    document.getElementById('generalo')?.addEventListener("change", function() {
      const selectedNamefajta = (document.querySelector('input[type="radio"][name="namefajta"]:checked') as HTMLInputElement)?.value;
      if (selectedNamefajta === "a") {
        allapotok.forEach(allapot => {
          (allapot as HTMLInputElement | HTMLLabelElement).style.visibility = "hidden";
        });
        document.getElementById("namefajta_c_extrafield").style.visibility = "hidden";
        document.getElementById("namefajta_j_extrafield").style.visibility = "hidden";
      } else {
        allapotok.forEach(allapot => {
          (allapot as HTMLInputElement | HTMLLabelElement).style.visibility = "visible";
        });
        const selectedAllapot = (document.querySelector('input[type="radio"][name="nameallapot"]:checked') as HTMLInputElement)?.value;
        if ((selectedNamefajta === "c" || selectedNamefajta === "j") && (selectedAllapot < "l8")) {
          if (selectedNamefajta === "c") {
            document.getElementById("namefajta_c_extrafield").style.visibility = "visible";
            document.getElementById("namefajta_j_extrafield").style.visibility = "hidden";
          } else if (selectedNamefajta === "j") {
            document.getElementById("namefajta_c_extrafield").style.visibility = "hidden";
            document.getElementById("namefajta_j_extrafield").style.visibility = "visible";
          }
        } else {
          document.getElementById("namefajta_c_extrafield").style.visibility = "hidden";
          document.getElementById("namefajta_j_extrafield").style.visibility = "hidden";
        }
      }
    });

    const table = document.getElementById('gpkPhDKozlemenyek');
    if (table) {
      // csak ha létezik a #gpkPhDKozlemenyek táblázat. ENnek szükséges feltétele, hogy a GPK PhD pontozó részletező nézetében vagyunk

      // egyedi közlemény-metaadatok generálása
      let allPubidsCSV = table.getAttribute('mtmt-all_pubids');
      let url = this.clientConfig.config.mtmt2.publication;
      fetch(url.replace('@@@', allPubidsCSV))
      .then((response) => response.json())
      .then((data) => {
        for (const publication of data.content) {
          try {
            let row = document.getElementById(publication.mtid);
            let firstCell = row.querySelector('.gpk_phd_publication_table_row');
            // clone node to retain attributes for debugging purposes
            const newDiv = firstCell.cloneNode(false) as HTMLElement;

            // process authors only
            const authors = publication.authorships
              .filter(authorship => authorship.type.otype == 'AuthorshipType' && authorship.type.mtid == 1) //AuthorshipType/mtid=1 is author
              .map(authorship => (authorship.otype == 'PersonAuthorship')?((authorship.author)?`${authorship.author.familyName} ${firstCharHungarian(authorship.author.givenName)}.`:`${nameAbbreviation(authorship.label)}` ):`${authorship.label}`);
            const authorContent = document.createTextNode(`${authors.join(', ')}: `);
            newDiv.appendChild(authorContent);

            const titleNode = document.createElement("a");
            titleNode.textContent = publication.title;
            titleNode.setAttribute('href', `https://m2.mtmt.hu/api/publication?format=template&cond=mtid;in;${publication.mtid}`);
            titleNode.setAttribute('class', 'gpk_phd_external_link');
            newDiv.append(titleNode, '. ');

            const pubType = firstCell.getAttribute('data-pubtype');
            if (pubType === "j" || pubType === "bc" || pubType === "c") {
              // Look for container metadata
              let In = publication?.book?.title ?? publication?.journal?.title;
              if(In){
                const others = document.createElement("span");
                others.textContent = `${In}, ${publication.publishedYear}. ${publication.pageLength} p.`;
                newDiv.appendChild(others);

                firstCell.replaceWith(newDiv);
              } else {
                const containerId = firstCell.getAttribute('data-pubtype_container_id');
                const container_url = this.clientConfig.config.gpk_phd_container_urls[pubType];
                if (container_url && containerId) {
                  fetch(container_url.replace('@@@', containerId))
                  .then((response) => response.json())
                  .then((containerData) => {
                    In = containerData?.content?.title;
                    const felteteles = document.createElement("span");
                    felteteles.className = "felteteles";
                    felteteles.textContent = `${In}, ${publication.publishedYear}.`;
                    newDiv.appendChild(felteteles);

                    firstCell.replaceWith(newDiv);
                  });
                }
              }
            } else if (pubType === "b"){
              const others = document.createElement("span");

              const publisherNamePlace = publication?.publishers.map(publisher => publisher.name+', '+(publisher?.cities.map(city => city.label) ?? '')).join(', ') ?? '';
              if (publisherNamePlace) {
                others.append(publisherNamePlace, ', ')
              }

              others.append(`${publication.publishedYear}. ${publication.pageLength} p.`);

              newDiv.appendChild(others);
              firstCell.replaceWith(newDiv);
            }
          } catch (error) {
            console.error(error);
          }
        }
      })
      .catch(console.error);
    }
  }

  addHighlightHandler(event){
    let highlighteds = this.container.nativeElement.querySelectorAll('.highlight');
    highlighteds.forEach(highlighted => highlighted.classList.remove('highlight'));
    let pubIds: string = event.currentTarget.getAttribute('data-pubids');
    let pubIdsNotEmpty = pubIds && this.formatIds(pubIds).length > 0;
    if (pubIdsNotEmpty) {
      this.formatIds(pubIds).split(',').forEach(id => {
        let element = document.getElementById(id)
        if(element){
          element.classList.add('highlight');
        }
      });
    }

    let disableHighlightsButton = document.getElementById('disable-highligths-button');

    if(disableHighlightsButton){
      if(disableHighlightsButton !== event.currentTarget && pubIdsNotEmpty){
          disableHighlightsButton.style.display = "block";
      } else {
        disableHighlightsButton.style.display = "none";
      }
    }
  }

  toggleVisibility(event){
    let togleabbleId: string = event.currentTarget.getAttribute('toggleable-id');
    let displayMode: string = event.currentTarget.getAttribute('display-mode') || 'block';

    var x = document.getElementById(togleabbleId);
    if (x.style.display === "none") {
      event.currentTarget.innerHTML = event.currentTarget.innerHTML.replace('kinyit', 'bezár');
      x.style.display = displayMode;
    } else {
      event.currentTarget.innerHTML = event.currentTarget.innerHTML.replace('bezár', 'kinyit');
      x.style.display = "none";
    }
  }

  exportToSpreadsheet(): void
  {
    // source: https://jsonworld.com/demo/how-to-export-data-to-excel-file-in-angular-application

    /* pass here the table id */
    let element = document.getElementById(this.exportableTableID);
    const ws: XLSX.WorkSheet =XLSX.utils.table_to_sheet(element);

    /* generate workbook and add the worksheet */
    const wb: XLSX.WorkBook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'TudriportSheet1');

    /* generate timestamp for embedding into the filename */
    let ts_now = new Date();

    let year = ts_now.getFullYear();
    let month = ts_now.getMonth()+1;
    let day = ts_now.getDate();

    let hour = ts_now.getHours();
    let min = ts_now.getMinutes();

    let ts_string = "" + year + "-" + (month<10?"0":"") + month + "-" + (day<10?"0":"") + day + "_" + (hour<10?"0":"") + hour + "_" + (min<10?"0":"") + min;

    /* save to file */
    XLSX.writeFile(wb, 'tudriport-list-export_'+ts_string+'.xlsx');
  }

  generateUrlGpkPhd(event){
    const gpkEpoch = new Date("2025-01-01T00:00:00Z");
    const now = new Date();
    const gpkTimestamp = Math.floor( (now.getTime() - gpkEpoch.getTime()) / 1000 );
    try{
      const type =  (<HTMLInputElement>document.querySelector('input[type="radio"][name="namefajta"]:checked'))?.value;
      let level = (<HTMLInputElement>document.querySelector('input[type="radio"][name="nameallapot"]:checked'))?.value;
      const thesis = (<HTMLInputElement>document.querySelector('input[type="radio"][name="nametezispont"]:checked'))?.value;
      if (type == null || thesis == null) {
        this.notificationManager.add("Mindhárom sor egy mezője kiválasztandó (kivéve automatikusan beazonosítható közleményfajta esetén)!", NotificationType.error);
        return;
      }
      if(type != 'a' && level == null){
        this.notificationManager.add("Vagy automatikusan beazonosíthatónak kell lennie, vagy választani kell állapotot!", NotificationType.error);
        return;
      }
      if(type == 'a'){
        level = 'l';
      }
      let typeContainerId:string = '';
      if (type === 'j' && level < 'l8') {
        typeContainerId = (<HTMLInputElement>document.getElementById('namefajta_j_extrafield')).value.trim();
        if (!typeContainerId) {
          this.notificationManager.add("Töltse ki a folyóirat MTMT azonosítóját, ha a közlemény állapota l7 vagy korábbi!", NotificationType.error);
          return;
        }
        if (!typeContainerId.match(/^[0-9]*$/)) {
          this.notificationManager.add("A folyóirat MTMT azonosítója csak számjegyekből állhat!", NotificationType.error);
          return;
        }
      } else if (type === 'c' && level < 'l8') {
        typeContainerId = (<HTMLInputElement>document.getElementById('namefajta_c_extrafield')).value.trim();
        if (!typeContainerId) {
          this.notificationManager.add("Töltse ki a konferencia MTMT azonosítóját, ha a közlemény állapota l7 vagy korábbi!", NotificationType.error);
          return;
        }
        if (!typeContainerId.match(/^[0-9]*$/)) {
          this.notificationManager.add("A konferencia MTMT azonosítója csak számjegyekből állhat!", NotificationType.error);
          return;
        }
      }
      const text = `https://phd.gpk.bme.hu/pub/s/${type}${typeContainerId}/${level}/${thesis}?${gpkTimestamp}`;
      navigator.clipboard.writeText(text).then(() => {
        this.notificationManager.add(text + " vágólapra másolva", NotificationType.success);
      }).catch(() => {});
    }
    catch(exception){
      console.log(exception);
      this.notificationManager.add("Nem várt hiba történt az egyéb URL generálás során", NotificationType.error);
    }
  }
  copymegjegyzesGpkPhd(event){
    const text = document.getElementById('megjegyzes').innerText;
    navigator.clipboard.writeText(text).then(() => {
      this.notificationManager.add(text + " vágólapra másolva", NotificationType.success);
    }).catch(() => {});
  }
}
