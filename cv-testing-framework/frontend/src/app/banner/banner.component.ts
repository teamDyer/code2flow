import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { Router } from '@angular/router';

/* This implements the banner that is common across the top of all screens.
 * Users of this component can place items inside the menu by adding
 * them into the contents of the <app-banner> tag. */

@Component({
    selector: 'app-banner',
    templateUrl: './banner.component.html',
    styleUrls: ['./banner.component.css']
})
export class BannerComponent implements OnInit {

    topLevelPath: string = "";
    loggedIn: boolean = false;
    username: string = "";

    constructor(private api: ApiService, private router: Router) { }

    ngOnInit() {
        const components = window.location.href.split('/');
        this.topLevelPath = components[3] || '';
        this.getLoginStatus();
    }

    logout() {
        this.api.logout().subscribe(event => {
            window.location.href = "/home";
        });
    }

    getLoginStatus() {
        this.api.loginStatus().subscribe(data => {
            if (data.status === "logged_in") {
                this.username = data.username
                this.loggedIn = true;
            } else {
                this.loggedIn = false;
            }
        });
    }

}
