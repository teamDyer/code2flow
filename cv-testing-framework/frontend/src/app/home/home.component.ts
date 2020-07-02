import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
    selector: 'app-home',
    templateUrl: './home.component.html',
    styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {

    showLogin: boolean = false;
    showStatus: boolean = false;
    username: string = "";

    testNameFilter: string = "";

    allTests: Array<any> = [];

    constructor(private api: ApiService) { }

    ngOnInit() {
        this.getLoginStatus();
    }

    checkSubseq(str1: string, str2: string): boolean {
        let m = str1.length - 1;
        let n = str2.length - 1;
        while (m >= 0) {
            if (n < 0) return false;
            if (str1.charCodeAt(m) == str2.charCodeAt(n)) {
                m -= 1;
            }
            n -= 1;
        }
        return true; 
    }

    get testsToShow(): Array<any> {
        let caseInsensitiveFilter = this.testNameFilter.toLowerCase();
        return this.allTests
            .filter(x => this.checkSubseq(caseInsensitiveFilter, x.fullname.toLowerCase()));
    }

    getAvailableTests() {
        this.api.rawget('/api/results/all-tests/all').subscribe(x => {
            this.allTests = x;
            x.forEach(y => y.fullname = y.name + y.system)
        });
    }

    getLoginStatus() {
        this.api.loginStatus().subscribe(data => {
            if (data.status === "logged_in") {
                this.showStatus = true;
                this.username = data.username
                this.getAvailableTests();
            } else {
                this.showLogin = true;
            }
        })
    }

}
