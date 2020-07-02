import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-ops',
  templateUrl: './ops.component.html',
  styleUrls: ['./ops.component.css']
})

export class OpsComponent implements OnInit {

  panelOpenState: boolean = false;
  
  constructor(private api: ApiService) { }
  
  teams;
  err;
  ops;
  team;
  days;
  open_since = [30, 60, 90, 120, 150, 180];

  ngOnInit() {
    this.getTeamInfo()
  }

  getTeamInfo(){
    this.api.getAllTeams()
    .subscribe(
      res => {
        this.teams = res;
      },
      err => {
        this.err = err;
      }
    );
  };

  getOpsDetails(){
    this.api.getOpsByTeam(this.team)
    .subscribe(
      res => {
        this.ops = res;
      },
      err => {
        console.log(err)
      }
    );
  }

}
