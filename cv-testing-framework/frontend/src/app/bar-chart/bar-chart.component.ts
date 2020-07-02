import { Component, OnInit, ElementRef, Input, ViewChild, Output, EventEmitter } from '@angular/core';
import { Chart } from 'chart.js';
import { geoMeanPoints, makeDataset, colorForLabel } from '../chartjs-util';
import { GraphPointInspectorComponent } from '../graph-point-inspector/graph-point-inspector.component';

export interface BarChartBar {
  label: string;
  x: string,
  y: number;
};

@Component({
  selector: 'app-bar-chart',
  templateUrl: './bar-chart.component.html',
  styleUrls: ['./bar-chart.component.css']
})
export class BarChartComponent implements OnInit {

  @Input() paramModel: object = {};

  // For point inspector
  public pointX: number;
  public pointY: number;
  
  renderError: string;
  private chartOptions: any;
  private chart: any;
  private labels: Array<string>;
  title?: string = null;
  private rows: Array<BarChartBar> = [];
  public pointShow: boolean = false;

  failedToRender: boolean = false;

  @ViewChild("chartCanvas", { static: true })
  chartCanvas: ElementRef;

  @ViewChild("pointInspector", { static: true })
  pointInspector: GraphPointInspectorComponent;

  constructor() { }

  ngOnInit() {
  }

  rerender() {
    try {
      this.chartConfig();
      this.failedToRender = false;
    } catch (error) {
      this.failedToRender = true;
      this.renderError = String(error);
    }
    this.resize();
  }

  @Input() set data(rows: Array<BarChartBar>) {
    this.rows = rows;
    this.rerender();
  }

  @Output() hideLabelsChange = new EventEmitter<Array<string>>();
  @Input() set hideLabels(labels: Array<string>) {
    this.labels = labels;
    this.rerender();
  }

  resize() {
    // Add chart to DOM
    Chart.defaults.global.events = ["click"]
    let ctx = this.chartCanvas.nativeElement.getContext('2d');
    window.setTimeout(() => {
      if (this.chart) {
        this.chart.destroy();
      }
      this.chart = new Chart(ctx, this.chartOptions);
    }, 0);
    this.hideInspector();
  }

  hideInspector() {
    this.pointShow = false;
  }

  refresh() {
    this.chartConfig();
    this.resize();
  }

  chartConfig() { 
    // Massage the data from the backend into a form Chart.js can use.
    let xs = this.rows.map(el => el.x).filter((v, i, a) => a.indexOf(v) === i).sort();
    let labels = Array.from(new Set(this.rows.map(el => el.label)));
    let dataSets = []
    for (let label of labels) {
      // Map points x -> y
      let m = new Map();
      let fullm = new Map();
      this.rows.filter(a => a.label === label).forEach(a => {
        m.set(a.x, a.y);
        fullm.set(a.x, a)
      });
      dataSets.push({
        hidden: this.labels.indexOf(label) !== -1,
        label: label,
        backgroundColor: colorForLabel(label),
        borderColor: colorForLabel(label),
        data: xs.map(x => m.get(x)),
        fullData: xs.map(x => fullm.get(x))
      })
    }

    // Check if a field is supplied
    let notEmpty = (x) => ( !Number.isNaN(x) && x != '' && x != null );
    let hor = this.paramModel['horizontal']

    // Pass this nested object to chart.js for rendering
    this.chartOptions = {
      type: hor ? 'horizontalBar' : 'bar',
      data: {
        xLabels: hor ? [] : xs,
        yLabels: hor ? xs : [],
        datasets: dataSets
      },
      options: {
        title: {
          display: !!this.paramModel['title'],
          text: this.paramModel['title'],
          fontSize: 24
        },
        scales: {
          xAxes: [{
            stacked: this.paramModel['stacked'],
            ticks: {},
            scaleLabel: {
              display: !!this.paramModel[hor ? 'ylabel' : 'xlabel'],
              labelString: this.paramModel[hor ? 'ylabel' : 'xlabel']
            }
          }],
          yAxes: [{
            stacked: this.paramModel['stacked'],
            ticks: {},
            scaleLabel: {
              display: !!this.paramModel[hor ? 'xlabel' : 'ylabel'],
              labelString: this.paramModel[hor ? 'xlabel' : 'ylabel']
            }
          }]
        },
        display: true,
        maintainAspectRatio: false,
        animation: {
          duration: 0
        },
        hover: {
          animationDuration: 0
        },
        legend: {
          display: labels.length <= 30,
          onClick: (event, item) => {
            let globalHandler = Chart.defaults.global.legend.onClick.bind(this);
            globalHandler(event, item);
            let label = dataSets[item.datasetIndex].label;
            let labelIndex = this.labels.indexOf(label);
            if (labelIndex == -1) {
              this.labels.push(label);
            } else {
              this.labels.splice(labelIndex, 1);
            }
            this.hideLabelsChange.emit(this.labels);
          }
        },
        tooltips: {
          // Disable the on-canvas tooltip
          enabled: false,
          custom: (tooltipModel) => {
            // Get data
            if (!tooltipModel.dataPoints || tooltipModel.dataPoints.length < 1) {
              this.pointShow = false;
              return;
            }
            let dataPoint = tooltipModel.dataPoints[0];
            let datasetIndex = dataPoint.datasetIndex;
            let index = dataPoint.index;
            let dataObject = dataSets[datasetIndex].fullData[index];
            this.pointInspector.setModel(dataObject);

            // Tooltip Element
            let position = this.chart.canvas.getBoundingClientRect();
            let caret = {x: tooltipModel.caretX, y: tooltipModel.caretY};
            this.pointX = position.left + caret.x + window.pageXOffset;
            this.pointY = position.top + caret.y + window.pageYOffset;
            this.pointShow = tooltipModel.opacity !== 0;
          }
        }
      }
    }

    if (notEmpty(this.paramModel['min'])) {
      if (this.paramModel['horizontal']) {
        this.chartOptions.options.scales.xAxes[0].ticks['min'] = this.paramModel['min']
      } else {
        this.chartOptions.options.scales.yAxes[0].ticks['min'] = this.paramModel['min']
      }
    }

    if (notEmpty(this.paramModel['max'])) {
      if (this.paramModel['horizontal']) {
        this.chartOptions.options.scales.xAxes[0].ticks['max'] = this.paramModel['max']
      } else {
        this.chartOptions.options.scales.yAxes[0].ticks['max'] = this.paramModel['max']
      }
    }
  }
}
