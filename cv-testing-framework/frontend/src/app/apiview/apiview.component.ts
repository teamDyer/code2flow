import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
    selector: 'app-apiview',
    templateUrl: './apiview.component.html',
    styleUrls: ['./apiview.component.css']
})
export class ApiviewComponent implements OnInit {

    apiUrl: string = "/api/results/all";
    apiResult: string = null;
    apiLoading: boolean = false;
    apiError: string = null

    constructor(private api: ApiService) { }

    ngOnInit() {
    }

    go() {
        this.apiResult = null;
        this.apiLoading = true;
        this.apiError = null;
        this.api.rawget(this.apiUrl).subscribe(x => {
            this.apiLoading = false;
            this.apiResult = JSON.stringify(x, null, 2);
        }, err => {
            this.apiLoading = false;
            this.apiError = err.message;
        });
    }

}
