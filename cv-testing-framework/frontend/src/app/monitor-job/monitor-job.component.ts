import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service'

@Component({
    selector: 'app-monitor-job',
    templateUrl: './monitor-job.component.html',
    styleUrls: ['./monitor-job.component.css']
})
export class MonitorJobComponent implements OnInit {

    showVisualization: boolean = false;
    queryData: object[] = [];

    constructor(public api: ApiService){
    }
    ngOnInit() {
        this.getRunningJobs();
    }

    getRunningJobs() {
        this.api.getVRLRunningJobs().subscribe(responseData => {
            this.showVisualization = true;
            this.queryData = [].concat(responseData);
        })
    }

    refresh(){
        console.log("Refresh event is triggered");    
        this.getRunningJobs();    
      }
}
