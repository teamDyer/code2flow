import { Component, OnInit, Input, SimpleChanges } from '@angular/core';
import { ApiService } from '../api.service';
import { MatSnackBar } from '@angular/material/snack-bar';


@Component({
  selector: 'app-nvbugs',
  templateUrl: './nvbugs.component.html',
  styleUrls: ['./nvbugs.component.css']
})
export class NvbugsComponent implements OnInit {
  err: any;
  bugs = {};
  bug_id: number;
  showError: boolean = false;
  showSuccess: boolean = false;
  successMessage: string;
  errorMessage: string;
  showDelete: boolean = false;

  constructor(private api: ApiService, private snackBar: MatSnackBar) { }
  @Input() team_name: any;
  @Input() days: any;

  getBugsWithKeyword(team_name, days) {
    this.api.getBugsByKeyword(team_name, days)
      .subscribe(
        res => {
          this.processResponse(res)
        },
        err => {
          this.err = err;
        }
      );
  };

  getBugsWithoutKeyword(team_name, days) {
    this.api.getBugsByMembers(team_name, days)
      .subscribe(
        res => {
          this.processResponse(res)
        },
        err => {
          this.err = err;
        }
      );
  };

  getUserAddedBugs(team_name) {
    this.api.getUserAddedBugs(team_name)
      .subscribe(
        res => {
          this.processResponse(res)
        },
        err => {
          this.err = err;
        }
      );
  };

  processResponse(res) {
    for (let i of res) {
      let keyword: string;
      let keywords = i['CustomKeyword'].split(",")
      for (let j of keywords) {
        if (j.includes("comptest") || j.includes('user_added')) {
          keyword = j.trim();
        };
      };
      if (!this.bugs[keyword]) {
        this.bugs[keyword] = [];
      }
      let buginfo = {}
      buginfo["BugId"] = i['BugId'];
      buginfo["BugAction"] = i['BugAction'];
      buginfo["Synopsis"] = i['Synopsis'];
      this.bugs[keyword].push(buginfo);
    };
  };

  addBug() {
    this.api.add_bug_to_hub(this.bug_id, this.team_name)
      .subscribe(
        res => {
          this.showSuccess = true;
          this.successMessage = res;
          this.showError = false;
          this.showSnackBar('added')
          this.bug_id = null;
        },
        err => {
          this.showError = true;
          this.errorMessage = err.error;
        }
      );

  };

  deleteBug() {
    this.api.delete_bug_from_hub(this.bug_id, this.team_name)
      .subscribe(
        res => {
          this.showSuccess = true;
          this.successMessage = res;
          this.showSnackBar('deleted')
          this.bug_id = null;
          this.showDelete = false;
        },
        err => {
          this.showSuccess = false;
          this.errorMessage = err;
        }
      );
  };

  confirmDelete() {
    this.showDelete = true;
  };

  cancelDelete() {
    this.showDelete = false;
    this.showError = false;
    this.showSuccess = false;
  };

  getBugs() {
    this.bugs = {}
    this.getBugsWithKeyword(this.team_name, this.days);
    this.getBugsWithoutKeyword(this.team_name, this.days);
    this.getUserAddedBugs(this.team_name)
  }


  showSnackBar(message) {
    let panelclass = 'green-snackbar'
    if (message === 'deleted') {
      panelclass = 'red-snackbar';
    }
    this.snackBar.open("Bug " + message + " : " + <string><any>this.bug_id, " ", {
      duration: 3000,
      panelClass: [panelclass],
      verticalPosition: 'bottom',
      horizontalPosition: 'end'
    });
  }

  onChange() {
    this.showError = false;
  }

  ngOnChanges(changes: SimpleChanges) {
    this.getBugs()
  }
  ngOnInit() {

  }
}