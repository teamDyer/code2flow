import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service'
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-job',
  templateUrl: './job.component.html',
  styleUrls: ['./job.component.css']
})
export class JobComponent implements OnInit {

  showInfo: boolean = false;
  rowid: string = null;
  testSystem: string = null;
  testName: string = null;
  testInfo: any = null;
  subtests: any = null;

  constructor(private api: ApiService, private route: ActivatedRoute, private router: Router) { }

  refresh() {
    this.rowid = this.route.snapshot.paramMap.get('rowid');
    this.testName = this.route.snapshot.paramMap.get('testName');
    this.testSystem = this.route.snapshot.paramMap.get('testSystem');
    this.getJobInfo();
  }

  ngOnInit() {
    this.router.events.subscribe((e: any) => {
      if (e.url) {
        this.refresh();
      }
    });
    this.refresh();
  }

  makeKVPairs(obj) {
      return Object.entries(obj).map(([k, v]) => {
        // Create item to render
        let ret = {
          type: 'string',
          name: k.replace('_', ' '),
          value: v,
          href: ''
        }
        if (['notes'].includes(k)) {
          ret.type = 'pre';
        } else if (['original_id'].includes(k)) {
          // we link to the original job page if we can
          ret.type = 'link';
          if (this.testSystem == 'vrl') {
            ret.href = 'http://ausvrl/showjob.php?job=' + v;
          } else {
            ret.type = 'string';
          }
        } else if (['id'].includes(k)) {
          ret.type = 'none';
        } else if (['subtest_results'].includes(k)) {
          ret.type = 'table';
          ret.value = Object.entries(v);
        }
        return ret;
      }).sort((a, b) => (a.type + a.name).localeCompare(b.type + b.name))
  }

  getJobInfo() {
    this.showInfo = false;
    this.api.rawget('/api/results/one/' + this.testSystem + '/' + this.testName + '/' + this.rowid).subscribe(data => {
      this.showInfo = true;
      if (data.subtest_results) {
        this.subtests = this.makeKVPairs(data.subtest_results)
      }
      let data_sans_subtests = Object.assign({}, data);
      delete data_sans_subtests.subtest_results;
      this.testInfo = this.makeKVPairs(data_sans_subtests);
    });
  }

}