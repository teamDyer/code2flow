import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service'
import { FormGroup, FormControl } from '@angular/forms';

@Component({
    selector: 'app-submit-job',
    templateUrl: './submit-job.component.html',
    styleUrls: ['./submit-job.component.css']
})
export class SubmitJobComponent implements OnInit {

    // Some defaults.

    // The list of properties required to start a job here should eventually come from
    // the server and not correspond directly to VRL jobs - we want to be able to
    // work at a higher level than that.
    // server: string = "ausvrl";
    // operatingsystem: string = "win1064";
    // testname: string = "";
    // machine: string = "";
    // note: string = "";
    // response: string = "email";
    // driver_package: string = "";
    badSubmitError: string = "";
    badSubmit: boolean = false;

    waiting: boolean = false;
    showResults: boolean = false;
    resultJobs: any;
    // This property will hold all inputs available on submit form
    testSubmission: FormGroup

    constructor(public api: ApiService){
    }

    ngOnInit() {
        this.testSubmission = new FormGroup({
            testName: new FormControl(),
            package_source: new FormControl(),
            package_build: new FormControl(),
            operatingSystem: new FormControl(),
            package_branch: new FormControl(),
            package_name: new FormControl(),
            package_id: new FormControl(),
            package_urls: new FormControl(),
            isolation_mode: new FormControl(),
            first_changelist: new FormControl(),
            last_changelist: new FormControl(),
            selected_changelists: new FormControl(),
            package_changelist: new FormControl(),
            server: new FormControl(),
            machine: new FormControl(),
            response: new FormControl(),
            note: new FormControl(),
            test_system: new FormControl(),
            test_names: new FormControl([]),
            gpu_names: new FormControl([]),
            machine_names: new FormControl([]),
            machinepool_name: new  FormControl([]),
            machine_name_local: new FormControl()
        });
        // this.testSubmission.valueChanges.subscribe(newVal => console.log(newVal))
    }

    submitJob() {
        this.waiting = true;
        console.log("Submitting a job...");
        this.badSubmit = false;
        let formData = this.testSubmission.getRawValue()
        let os = null
        if(formData.operatingSystem)
            os = formData.operatingSystem.value
        let postData = {
            // server: formData.server
            server: "ausvrl",
            operatingsystem: os,
            testname: formData.testName,
            machine: formData.machine,
            response: formData.response,
            package: formData.package_name,
            changelist: formData.package_changelist,
            package_urls: formData.package_urls,
            isolation_mode: formData.isolation_mode,
            note: formData.note,
            test_system:formData.test_system,
            test_names:formData.test_names,
            gpu_names:formData.gpu_names,
            machine_names:formData.machine_names
        }
        console.log(postData)
        this.api.submitVRLTest(postData).subscribe(x => {
            this.waiting = false;
            this.showResults = true;
            this.resultJobs = x.join(", ");
            this.badSubmit = false;
        }, err => {
            console.log(err)
            this.badSubmitError = String(err.error.error ? err.error.error : err.error);
            this.badSubmit = true;
            this.waiting = false;
        })
    }

}
