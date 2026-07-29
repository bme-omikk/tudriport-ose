import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import { ExtAuthorService } from '../../api/services/ext-author.service'
import { ExtAuthor } from '../../api/models/ext-author'
import { NotificationManager, NotificationType } from '../../notification-manager'

@Component({
  selector: 'app-ext-author-import',
  templateUrl: './ext-author-import.component.html',
  styleUrls: ['./ext-author-import.component.css'],
})
export class ExtAuthorImportComponent implements OnInit {
  data: ExtAuthor = new ExtAuthor;
  errors: ExtAuthor;
  working = false;  

  constructor(private extAuthService: ExtAuthorService,
              private notificationManager: NotificationManager) { }

  ngOnInit() {
  }

  onFileChange($event) {
    // store content of selected file
    let fileReader = new FileReader();
    let data = this.data
    fileReader.onloadend = function(e){
      data.file_data = fileReader.result as string;
    }
    let inputFile = $event.target.files[0];
    fileReader.readAsText(inputFile);
  }

  handleResponse(errors?: ExtAuthor) {
    if (errors) {
      this.errors = errors;
    } else {
      this.notificationManager.add("Sikeres művelet!", NotificationType.success);
      this.errors = null;
    }
  }

  submit() {
    this.working = true;
    this.extAuthService.createFromFile(this.data).pipe(finalize(() => this.working = false)).subscribe(data => this.handleResponse(data));
  }

}
