import { Component, OnInit, Input } from '@angular/core';
import { ExportToCsv } from 'export-to-csv';

@Component({
  selector: 'app-exportcsv',
  templateUrl: './exportcsv.component.html',
  styleUrls: ['./exportcsv.component.css']
})
export class ExportcsvComponent implements OnInit {

  @Input() name: string;
  @Input() data: any;

  constructor() { }

  export_data_to_csv(){
    const options = { 
      fieldSeparator: ',',
      filename: this.name +'_'+ Date(),
      quoteStrings: '"',
      decimalSeparator: '.',
      showLabels: true, 
      showTitle: false,
      useTextFile: false,
      useBom: true,
      useKeysAsHeaders: true,
    };
    const csvExporter = new ExportToCsv(options);
    csvExporter.generateCsv(this.data);
  };

  ngOnInit() {
  }

}
