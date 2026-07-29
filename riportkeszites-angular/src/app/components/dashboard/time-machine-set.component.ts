import { Component } from '@angular/core';
import { UserUtil } from 'src/app/user-util';

@Component({
    selector: 'app-time-machine-set',
    templateUrl: 'time-machine-set.component.html',
    styleUrls: ['time-machine-set.component.scss']
})
export class TimeMachineSetComponent { 
    permission: boolean = false;
    public static timeMachineDate: string = null;
    constructor(private userUtil: UserUtil){}
    ngOnInit(){
        this.userUtil.hasPerm('riport.view_admin_page').subscribe(p => this.permission = p);
    }
    set(time: string){
        TimeMachineSetComponent.timeMachineDate = time;
    }
}