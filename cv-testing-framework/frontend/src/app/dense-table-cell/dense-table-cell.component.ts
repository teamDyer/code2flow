import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';

@Component({
  selector: 'app-dense-table-cell',
  templateUrl: './dense-table-cell.component.html',
  styleUrls: ['./dense-table-cell.component.css']
})
export class DenseTableCellComponent implements OnInit {

  @Input() header: string = '';
  @Input() data: any = '';
  @Input() mapping: object = null;

  show: boolean = false;

  constructor() { }

  ngOnInit() {
  }

  makeLink(str) {
      let patt = this.mapping[this.header];
      return patt.replace('$', str);
  }

  isAbsoluteLink() {
      let patt = this.mapping[this.header];
      return patt.includes('//');
  }

  cellKind() {
    // use an empty header to indicate a leaf node.
    if (this.data == null) {
      return 'null';
    }
    if (Array.isArray(this.data)) {
      return 'array';
    }
    if (this.mapping && this.mapping[this.header]) {
      return 'link';
    }
    if (typeof this.data === 'object') {
      return 'object';
    }
    return 'default';
  }

  toggle() {
    this.show = !this.show;
  }

}
