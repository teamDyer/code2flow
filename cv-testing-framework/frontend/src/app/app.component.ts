import { Component, Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ErrorHandler } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

let globalSnacks: MatSnackBar = null;

/* A global error handler that shows a snackbar
 */
@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
    handleError(error) {
        if (error instanceof HttpErrorResponse && error.status === 403) {
            window.location.href = "/home";
        }
        console.log(error);
    }
}

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.css'],
    providers: [ApiService]
})
export class AppComponent {

    constructor(private api: ApiService, private snackBar: MatSnackBar) {
        globalSnacks = this.snackBar;
    }

}
