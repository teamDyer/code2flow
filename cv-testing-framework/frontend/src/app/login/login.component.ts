import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
    selector: 'app-login',
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

    username: string = "";
    password: string = "";
    loading: boolean = false;
    showBad: boolean = false;

    constructor(private api: ApiService) { }

    ngOnInit() {
    }

    login() {
        this.loading = true;
        this.showBad = false;
        this.api.login(this.username, this.password)
            .subscribe(event => {
                window.location.href = "/home";
            }, err => {
                this.showBad = true;
                this.loading = false;
            });
    }

}
