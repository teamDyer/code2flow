import { Component, OnInit, ViewChild } from '@angular/core';
import { ApiService } from '../api.service';
import { makeDataset } from '../chartjs-util';
import {MatTableDataSource} from '@angular/material/table';

export interface poolData {
  machine_name: string;
  gpu: string;
  pool_name: string;
};

@Component({
  selector: 'app-machine-monitoring',
  templateUrl: './machine-monitoring.component.html',
  styleUrls: ['./machine-monitoring.component.css']
})


export class MachineMonitoringComponent implements OnInit {
  err: string = null;
  machinePoolData = null;
  displayedColumns: string[] = ['machine_name', 'gpu', 'pool_name'];
  apiResult: string = null;
  xlabels: string = null;
  dataset;
  gd;
  mastergd={};
  days = 7;
  days_list = [7, 10, 14, 20, 30]
  filters = ["total time", "job count"]
  filter = this.filters[0];
  constructor(private api: ApiService) { }

  getmmdata(){
    this.filter = this.filter.replace(" ", "");
    this.api.getMachineMonitoringData(this.days, this.filter)
    .subscribe(
      res =>{
        this.apiResult = res;
        this.xlabels = res['dates'];
        this.dataset = this.makeDS(res['results']);
      },
      err => {
        console.log(err)
        this.err = err;
      }
    );
  }

  getMachinePoolData(){
    this.api.getMachinePoolData()
    .subscribe(
      res =>{
        this.machinePoolData =new MatTableDataSource(res);
      },
      err => {
        console.log(err)
        this.err = err;
      }
    );
  }

  makeDS(data){
    for(let i in data){
      let ds=[];
      for( let j in data[i]){
        ds.push(makeDataset(data[i][j], j, []));
      }
      this.mastergd[i]=ds;
    }
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.machinePoolData.filter = filterValue.trim().toLowerCase();
  }

  ngOnInit() {
    this.getmmdata()
    this.getMachinePoolData()
  }
}
