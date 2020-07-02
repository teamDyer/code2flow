import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { ActivatedRoute, Router } from '@angular/router';
import { RequestCache } from '../request-cache.service';
import { interval } from 'rxjs';
import { makeModelConform } from '../param-chooser/param-chooser.component'

@Component({
  selector: 'app-satellite-ui',
  templateUrl: './satellite-ui.component.html',
  styleUrls: ['./satellite-ui.component.css']
})
export class SatelliteUiComponent implements OnInit {

  // Route parameters
  selectedSatellite: any = null;
  subpage: string = '';
  itemid: string = '';

  // Various state
  availableSatellites: Array<any> = [];
  selectedSatelliteInfo: any = null;
  selectedTest: any = null;
  jobModel: object = {};
  allSubmissions: Array<any> = [];
  allJobs: Array<any> = [];
  submissionJobs: Array<any> = [];
  satelliteFullInfo: any = null;
  testParams: Array<any> = [];
  jobSpecs: Array<any> = [];
  logTooLarge: boolean = false;

  // Pagination
  rowsPerPage: number = 25;
  submissionsNumPages: number = 0;
  jobsNumPages: number = 0;
  currentPage: number = 1;

  // Submission parameters
  submissionParams: Array<object> = [
    {
      'name': 'parallel',
      'type': 'nat',
      'optional': false,
      'default': 1,
      'doc': 'How many jobs should run in parallel? A value of 0 gives maximum parallelism.'
    },
    {
      'name': 'note',
      'type': 'text',
      'optional': false,
      'doc': 'Some text to help identify the reason for this submission.'
    }
  ];
  submissionModel: any = {};

  // for single job and submission
  selectedJobInfo: Array<any> = [];
  selectedSubmissionInfo: Array<any> = [];
  selectedJobLog: string = 'stdout.log';
  selectedJobLogData: string = null;

  // Status and error message
  statusMessage: string = null;
  errorMessages: Array<any> = [];

  // Flags for spinners
  isSubmitting: boolean = false;

  // Add links to dense tables
  tableMapping = {
    'job_id': '../job/$',
    'job_ids': '../job/$',
    'submission_id': '../submission/$'
  };

  tableMapping2 = {
    'job_id': '../../job/$',
    'job_ids': '../../job/$',
    'submission_id': '../../submission/$'
  };

  // How to show job in a table
  jobCols = [
    'job_id', 'name', 'params', 'status', 'return_code', 'started', 'finished', 'submission_id', 'submitted'
  ];
  
  // How to show submission in a table
  submissionCols = [
    'submission_id', 'submitted', 'status', 'parallel', 'num_jobs', 'job_ids', 'note'
  ];

  constructor(private api: ApiService, private route: ActivatedRoute, private router: Router, private cache: RequestCache) { }

  get encodedSatellite() {
    return this.selectedSatellite ? btoa(this.selectedSatellite) : null;
  }

  ngOnInit() {
    this.updateAvailable();

    // every 5 seconds, if we are looking at a job or submission page, autorefresh
    interval(5000).subscribe(x => {
      if (this.subpage == 'job' && this.selectedJobInfo && this.selectedJobInfo[0].status === 'RUNNING') {
        if (['stdout.log', 'stderr.log'].indexOf(this.selectedJobLog) != -1) {
          this.getJobLogData();
        }
        this.getSelectedJob(false);
      } else if (this.subpage == 'submission') {
        if (this.selectedSubmissionInfo[0].status === 'RUNNING') {
          this.getSelectedSubmission();
        }
      }
    });

    this.route.paramMap.subscribe(x => {
      this.statusMessage = null;
      this.errorMessages = [];
      this.currentPage = 1;
      this.subpage = x.get('subpage');
      this.itemid = x.get('itemid');
      const newSatellite = atob(x.get('satellite') || '');
      if (newSatellite != this.selectedSatellite) {
        this.selectedSatellite = newSatellite;
        this.changeSatellite();
      }
      
      switch (this.subpage) {
        default:
          this.navigateSubpage('info');
          break;
        case null:
          if (this.selectedSatellite) {
            this.navigateSubpage('info');
          }
          break;
        case 'submit':
          this.getAvailable();
          break;
        case 'jobs':
          this.getJobs();
          break;
        case 'submissions':
          this.getSubmissions();
          break;
        case 'job':
          this.getSelectedJob();
          this.selectedJobLog = 'stdout.log';
          this.selectedJobLogData = null;
          this.getJobLogData();
          break;
        case 'submission':
          this.getSelectedSubmission();
          break;
        case 'info':
          this.getInfo();
          break;
      }
    });
  }

  handleError(err: string) {
    this.errorMessages.push(err);
  }

  clearError() {
    this.errorMessages = [];
  }

  // Update available satellite list
  updateAvailable() {
    this.api.rawget('/api/satellite/available').subscribe(x => {
      this.availableSatellites = x;
    }, err => {
      this.availableSatellites = [];
      this.handleError("Could not get available satellites");
    });
  }

  // Get something from the selected satellite
  getSatellite(path: string, reload=false) {
    if (reload) {
      this.cache.delete(this.selectedSatellite + path);
    }
    return this.api.externalGet(this.selectedSatellite + path);
  }

  // Post something from the selected satellite
  postSatellite(path: string, data: any, reload=false) {
    if (reload) {
      this.cache.delete(this.selectedSatellite + path);
    }
    return this.api.externalPost(this.selectedSatellite + path, data);
  }

  // Update parameter list for current test
  getParameters() {
    if (this.selectedTest) {
      let start = this.selectedTest;
      return this.getSatellite('/spec/' + this.selectedTest.name).subscribe(x => {
        if (start == this.selectedTest) {
          this.testParams = x.data.parameters;
        }
      }, err => {
        this.handleError('Could not get test parameters')
      });
    }
  }

  // Get all submissions
  getSubmissions() {
    let minIndex = (this.currentPage - 1) * this.rowsPerPage;
    let maxIndex = minIndex + this.rowsPerPage;
    return this.getSatellite('/submissions/range/' + minIndex + '/' + maxIndex, true).subscribe(x => {
      this.allSubmissions = x.data.slice;
      this.submissionsNumPages = Math.ceil(x.data.total / this.rowsPerPage);
    }, err => {
      this.allSubmissions = [];
      this.handleError("Could not get submissions");
    });
  }

  // Get all satellite jobs
  getJobs() {
    let minIndex = (this.currentPage - 1) * this.rowsPerPage;
    let maxIndex = minIndex + this.rowsPerPage;
    return this.getSatellite('/jobs/range/' + minIndex + '/' + maxIndex, true).subscribe(x => {
      this.allJobs = x.data.slice;
      this.jobsNumPages = Math.ceil(x.data.total / this.rowsPerPage);
    }, err => {
      this.allJobs = [];
      this.handleError("Could not get jobs");
    });
  }

  // Get jobs for the current submission
  getSubmissionJobs() {
    return this.getSatellite('/submission_jobs/' + this.itemid, true).subscribe(x => {
      this.submissionJobs = x.data;
    }, err => {
      this.submissionJobs = [];
      this.handleError("Could not get jobs for submission");
    })
  }

  // Get key value pairs of an object
  kvs(obj) {
    let pairs = [];
    for (let [k, v] of Object.entries(obj)) {
      pairs.push({key: k, value: v});
    }
    return pairs;
  }

  // Get satellite full info
  getInfo() {
    return this.getSatellite('/info', true).subscribe(x => {
      this.satelliteFullInfo = this.kvs(x.data);
    }, err => {
      this.satelliteFullInfo = null;
      this.handleError("Could not get information for satellite");
    });
  }

  // Get available tests
  getAvailable() {
    this.getSatellite('/available_tests', true).subscribe(x => {
      this.selectedSatelliteInfo = x.data;
    }, err => {
      this.selectedSatelliteInfo = [];
      this.handleError("Could not get available tests for satellite");
    })
  }

  // Get information on the selected job
  getSelectedJob(reset=true) {
    this.getSatellite('/job/' + this.itemid, true).subscribe(x => {
      this.selectedJobInfo = [x.data];
      if (!x.data.logs || (this.selectedJobLog && x.data.logs.indexOf(this.selectedJobLog) == -1)) {
        this.selectedJobLog = null;
      }
    }, err => {
      this.selectedJobInfo = null;
      this.handleError("Could not get information for selected job");
    })
  }

  // Get information on the selected job
  getSelectedSubmission() {
    this.getSatellite('/submission/' + this.itemid, true).subscribe(x => {
      this.selectedSubmissionInfo = [x.data];
    }, err => {
      this.selectedSubmissionInfo = null;
      this.handleError("Could not get information for selected submission");
    })
    this.getSubmissionJobs();
  }

  // Try to cancel the selected job
  cancelSelectedJob() {
    this.postSatellite('/cancel_job/' + this.itemid, true).subscribe(x => {
      this.getSelectedJob();
    }, err => {
      this.handleError("Could not cancel job");
    })
  }

  // Try to cancel the selected submission
  cancelSelectedSubmission() {
    this.postSatellite('/cancel_submission/' + this.itemid, true).subscribe(x => {
      this.getSelectedSubmission();
    }, err => {
      this.handleError("Could not cancel submission");
    });
  }

  // Get a certain log file
  getJobLogData() {
    this.getSatellite('/job/' + this.itemid + '/log/' + this.selectedJobLog, true).subscribe(x => {
      this.logTooLarge = false;
      this.selectedJobLogData = x.data;
    }, err => {
      this.selectedJobLogData = null;
      if (err.error && err.error.data && typeof(err.error.data) == 'object') {
        this.logTooLarge = true;
      } else {
        this.handleError("Could not get log information for job");
      }
    })
  }

  navigateSubpage(path: string) {
    this.router.navigateByUrl('/satellite/' + this.encodedSatellite + '/' + path);
  }

  setSatellite() {
    let state = {};
    if (this.subpage) { state['subpage'] = this.subpage; }
    if (this.itemid) { state['itemid'] = this.itemid; }
    if (this.encodedSatellite) { state['satellite'] = this.encodedSatellite; }
    if (this.itemid) {
      this.router.navigate(['/satellite/' + this.encodedSatellite + '/' + this.subpage + '/' + this.itemid, state]);
    } else if (this.subpage != null) {
      this.router.navigate(['/satellite/' + this.encodedSatellite + '/' + this.subpage, state]);
    } else {
      this.router.navigate(['/satellite/' + this.encodedSatellite + '/info', state]);
    }
  }

  // Called when a new satellite is picked.
  changeSatellite() {
    this.selectedTest = null;
    this.selectedSatelliteInfo = null;
    this.jobSpecs = [];
  }

  // Called when a satellite test script is selected
  changeTest() {
    this.testParams = this.selectedTest.spec.parameters;
    this.getParameters();
  }

  // Add a job spec
  addSpec() {
    let ps = {};
    for (let e of this.testParams) {
      let v = this.jobModel[e.name];
      if (v != null) {
        ps[e.name] = v;
      }
    }
    // Try to coece model, and then check if it fully valid.
    makeModelConform(this.testParams, this.jobModel);
    if (!makeModelConform(this.testParams, this.jobModel, true)) {
      this.handleError('Invalid job spec')
      return;
    }
    this.jobSpecs.push({
      "name": this.selectedTest.name,
      "params": ps
    });
  }

  // Remove a job spec
  removeSpec(i: number) {
    this.jobSpecs.splice(i, 1);
  }

  // Clone a spec
  cloneSpec(i: number) {
    let name = this.jobSpecs[i].name;
    this.selectedTest = this.selectedSatelliteInfo.valid.find(x => x.name == name);
    this.jobModel = Object.assign({}, this.jobSpecs[i].params);
    this.changeTest();
  }

  _quoteOne(x: any) {
    let s = String(x);
    if (s.indexOf(' ') == -1) {
      return s;
    }
    return '"' + s.replace('"', '\\"') + '"';
  }

  // Make CLI string for showing pending job specs
  makeCliString(spec) {
    let keys = Array.from(Object.keys(spec.params));
    let items = keys.sort().map(x => '--' + x + '=' + this._quoteOne(spec.params[x]));
    return spec.name + '/run ' + items.join(' ')
  }

  refresh() {
    this.getJobs();
    this.getSubmissions();
  }

  // Submit
  submit() {
    this.clearError();
    this.statusMessage = null;
    this.isSubmitting = true;
    let specs = this.jobSpecs;
    this.jobSpecs = [];
    this.postSatellite('/run', Object.assign({
      job_specs: specs
    }, this.submissionModel)).subscribe(x => {
      this.isSubmitting = false;
      this.refresh();
      this.statusMessage = x.data;
    }, err => {
      this.isSubmitting = false;
      this.handleError(err.data);
      this.refresh();
    });
  }

  // Remove an error message
  dropError(i: number) {
    this.errorMessages.splice(i, 1);
  }

}
