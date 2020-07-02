import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-dense-table',
  templateUrl: './dense-table.component.html',
  styleUrls: ['./dense-table.component.css']
})
export class DenseTableComponent implements OnInit {

  rows: object[];
  headers: string[] = [];
  cellLimit: number = 0;
  cells: WeakMap<object, string>;
  rowsPerPage: number = 50;
  currentPage: number = 1;

  @Input() paramModel: object;
  @Input() columns: Array<string> = null;
  @Input() mapping: object = null;
  @Input() showCounts: boolean = false;
  @Input() autoPaginate: boolean = false;

  constructor() { }

  @Input() set data(value: object[]) {
    if (value == null) {
      value = [];
    }
    this.rows = value;
    this.currentPage = 1;
    if (this.columns) {
      this.headers = this.columns;
    } else if (this.rows.length > 0) {
      this.headers = Array.from(Object.keys(this.rows[0])).sort();
    } else {
      this.headers = [];
    }
  }

  get numPages() {
    return Math.ceil(this.rows.length / this.rowsPerPage);
  }

  get data() {
    if (this.autoPaginate) {
      let startIndex = (this.currentPage - 1) * this.rowsPerPage;
      let endIndex = (this.currentPage) * this.rowsPerPage;
      return this.rows.slice(startIndex, endIndex);
    } else {  
      return this.rows;
    }
  }

  // Get a kind of row to display. Basically, we
  // can special case different header names and types here.
  rowKind(header: string, row: any): string {
    if (header === 'id') {
      return 'jobid';
    }
    if (Array.isArray(row)) {
      return 'array';
    }
    if (typeof row === 'object') {
      return 'object';
    }
    return 'default';
  }

  ngOnInit() {
  }

}
