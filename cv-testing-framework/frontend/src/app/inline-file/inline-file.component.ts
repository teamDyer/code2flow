import { Component, OnInit, Input } from '@angular/core';

@Component({
    selector: 'app-inline-file',
    templateUrl: './inline-file.component.html',
    styleUrls: ['./inline-file.component.css']
})
export class InlineFileComponent implements OnInit {

    @Input() bodyText: string = "";
    @Input() fileName: string = "";

    constructor() { }

    ngOnInit() {

    }

}
