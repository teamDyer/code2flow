import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { colorForLabel } from '../chartjs-util';
import { GraphPointInspectorComponent } from '../graph-point-inspector/graph-point-inspector.component';
import { Chart } from 'chart.js';
import { RouteConfigLoadStart } from '@angular/router';

export interface PieSlice {
  name: string;
  value: number;
}

@Component({
  selector: 'app-pie-chart',
  templateUrl: './pie-chart.component.html',
  styleUrls: ['./pie-chart.component.css']
})
export class PieChartComponent implements OnInit {

  @Input() paramModel: object = {};

  // For point inspector
  public pointX: number;
  public pointY: number;

  slices: Array<PieSlice> = [];
  
  renderError: string;
  private chartOptions: any;
  private chart: any;
  title?: string = null;
  public pointShow: boolean = false;

  failedToRender: boolean = false;

  @ViewChild("chartCanvas", { static: true })
  chartCanvas: ElementRef;

  @ViewChild("pointInspector", { static: true })
  pointInspector: GraphPointInspectorComponent;

  constructor() { }

  ngOnInit() {
  }

  @Input() set data(slices: Array<PieSlice>) {
    this.slices = slices;
    try {
      this.chartConfig();
      this.failedToRender = false;
    } catch (error) {
      this.failedToRender = true;
      this.renderError = String(error);
    }
    this.resize();
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
    let labels = this.slices.map(el => el.name);
    let sizes = this.slices.map(el => el.value);
    let colors = labels.map(colorForLabel);
    let fullData = this.slices;
    let dataSets = [{
      data: sizes,
      backgroundColor: colors,
      fullData: fullData
    }];

    // Pass this nested object to chart.js for rendering
    this.chartOptions = {
      type: 'pie',
      data: {
        datasets: dataSets,
        labels: labels
      },
      options: {
        title: {
          display: !!this.paramModel['title'],
          text: this.paramModel['title'],
          fontSize: 24
        },
        display: true,
        maintainAspectRatio: false,
        animation: {
          duration: 0
        },
        hover: {
          animationDuration: 0
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
  }
}
