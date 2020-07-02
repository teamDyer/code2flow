import { Component, OnInit, ViewChild, Input } from '@angular/core';
import { Chart } from 'chart.js'

@Component({
  selector: 'app-lineg',
  templateUrl: './lineg.component.html',
  styleUrls: ['./lineg.component.css']
})
export class LinegComponent implements OnInit {
  @ViewChild('lineChart', { static: true }) private chartRef;
  constructor() { }

  @Input() xaxisLabels;
  @Input() dataSets;
  @Input() chartHeader;
  @Input() yaxisLabel: string;
  
  chart: any;

  displayChart(xs, ds) {
    this.chart = new Chart(this.chartRef.nativeElement, {
      type: 'line',
      data: {
        xLabels: xs,
        datasets: ds
      },
      options: {
        title: {
          display: true,
          text: this.chartHeader
        },
        display: true,
        responsive: false,
        maintainAspectRatio: false,
      scales: {
        yAxes: [{
          scaleLabel: {
            display: true,
            labelString: this.yaxisLabel
          }
        }]
      }
    }
    }

    )
  }

  ngOnInit() {
    this.displayChart(this.xaxisLabels, this.dataSets)
  }

}
