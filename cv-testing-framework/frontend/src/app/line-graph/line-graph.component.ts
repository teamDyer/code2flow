import { Component, OnInit, Input, ViewChild, ElementRef, Output, EventEmitter } from '@angular/core';
import { Chart } from 'chart.js';
import { geoMeanPoints, diffPercent, makeDataset, DataSet, zScore, zScorePoints } from '../chartjs-util';
import { GraphPointInspectorComponent } from '../graph-point-inspector/graph-point-inspector.component';

// Interface expected from database query
interface LineGraphRow {
  x: number;
  y: number;
  label: string;
};

// Get a function that gets rawdata from the dataset and
// transforms it into post processed data.
function getDatasetXForm(ds: DataSet) {
  switch (ds.params['post']) {
    case 'geomean':
      return y => diffPercent(ds.geomean, y);
    case 'zscore':
      return y => zScore(ds.geomean, ds.geostddev, y);
    default:
      return y => y;
  }
}

// Extend our line chart with custom box and whisker plot, and other niceties.
// See https://www.chartjs.org/docs/latest/developers/charts.html on extending
// Chart.js charts.
// This creates a new chart type 'lineWithBars' which is our custom
// extension of a line graph.
Chart.defaults.lineWithBars = Chart.defaults.line;
Chart.controllers.lineWithBars = Chart.controllers.line.extend({
    draw: function(ease) {
        Chart.controllers.line.prototype.draw.call(this, ease);
        let meta = this.getMeta();
        let ctx = this.chart.ctx;
        let datasets = this.chart.config.data.datasets;
        ctx.save();
        ctx.lineWidth = 1;
        for (let pt of meta.data) {
          let ys = pt._yScale;
          let ds = datasets[pt._datasetIndex];
          ctx.strokeStyle = ds.borderColor;
          ctx.beginPath();

          // We need a transform to handle geomean code.
          let xform = getDatasetXForm(ds);

          let a = ds.fullData[pt._index];
          
          // Draw a range for a single point.
          let ymin = ys.getPixelForValue(xform(a['y_max']));
          let ymax = ys.getPixelForValue(xform(a['y_min']));
          ctx.moveTo(pt._view.x - 5, ymin);
          ctx.lineTo(pt._view.x + 5, ymin);
          ctx.moveTo(pt._view.x - 5, ymax);
          ctx.lineTo(pt._view.x + 5, ymax);
          ctx.moveTo(pt._view.x, ymin);
          ctx.lineTo(pt._view.x, ymax);
          ctx.stroke();
        }
        ctx.restore();
    }
});

@Component({
  selector: 'app-line-graph',
  templateUrl: './line-graph.component.html',
  styleUrls: ['./line-graph.component.css']
})
export class LineGraphComponent implements OnInit {

  @Input() paramModel: object = {};
  
  renderError: string;
  private rows: Array<LineGraphRow>;
  private labels: Array<string>;
  private chartOptions: any;
  private chart: any;
  title?: string = null;

  failedToRender: boolean = false;

  @ViewChild("chartCanvas", { static: true })
  chartCanvas: ElementRef;

  @ViewChild("pointInspector", { static: true })
  pointInspector: GraphPointInspectorComponent;

  // Input to point inspector
  public pointX: number;
  public pointY: number;
  public pointShow: boolean = false;

  rerender() {
    try {
      this.lineChartConfig();
      this.failedToRender = false;
    } catch (error) {
      this.failedToRender = true;
      this.renderError = String(error);
    }
    this.resize();
  }

  @Input() set data(rows: Array<LineGraphRow>) {
    this.rows = rows;
    this.rerender();
  }

  @Output() hideLabelsChange = new EventEmitter<Array<string>>();
  @Input() set hideLabels(labels: Array<string>) {
    this.labels = labels;
    this.rerender();
  }

  hideInspector() {
    this.pointShow = false;
  }

  refresh() {
    this.lineChartConfig();
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

  // Get callback for chart.js to render y-axis ticks
  getTickCallback() {
    switch (this.paramModel['post']) {
      case 'geomean':
        return (value => {
          return Math.round(value * 10000) / 10000 + '%';
        });
      case 'zscore':
        return (value => {
          return '' + value + ' \u03c3';
        });
      default:
        return (x => x);
    }
  }

  constructor() { }

  ngOnInit() {
  }

  lineChartConfig() {
    // Fix existing links to geomean
    if (this.paramModel['geomean'] && !this.paramModel['post']) {
      this.paramModel['post'] = 'geomean';
    }
    // Massage the data from the backend into a form Chart.js can use.
    let xs = this.rows.map(el => el.x).filter((v, i, a) => a.indexOf(v) === i).sort();
    let labels = Array.from(new Set(this.rows.map(el => el.label)));
    let lines = new Map();
    this.title = this.paramModel['title'];
    for (let l of labels) {
      lines.set(l, {
        points: [],
        fullData: [],
        label: l
      });
    }
    for (let row of this.rows) {
      let line = lines.get(row.label);
      if (this.paramModel['drop_zeros'] && row.y === 0) {
        continue;
      }
      if (null == row.y) {
        throw new Error('Expected "y" column in data');
      }
      if (null == row.x) {
        throw new Error('Expected "x" column in data');
      }
      if (null == row.label) {
        throw new Error('Expected "label" column in data');
      }
      line.points.push({ x: row.x, y: row.y });
      line.fullData.push(row);
    }
    let dataSets = [];
    for (let line of Array.from(lines.values())) {
      let points;
      switch (this.paramModel['post']) {
        case 'geomean':
          points = geoMeanPoints(line.points);
          break;
        case 'zscore':
          points = zScorePoints(line.points);
          break;
        default:
          points = line.points;
          break;
      }
      let ds = makeDataset(points, line.label, line.fullData, this.paramModel)
      ds.hidden = this.labels.indexOf(line.label) != -1;
      dataSets.push(ds);
    }

    let notEmpty = (x) => ( !Number.isNaN(x) && x !== '' && x != null );

    let makeYAxis = () => {
      let ret = {
        position: this.paramModel['axis_on_right'] ? 'right' : 'left',
        ticks: {
          callback: this.getTickCallback()
        },
        scaleLabel: {
          display: !!this.paramModel['ylabel'],
          labelString: this.paramModel['ylabel']
        }
      }

      // Get min
      if (notEmpty(this.paramModel['ymin'])) {
        ret.ticks['min'] = Number(this.paramModel['ymin'])
      } else if (this.paramModel['intervals']) {
        // Need to manually calculate min if we have intervals
        let min = Infinity;
        for (let ds of dataSets) {
          let xform = getDatasetXForm(ds);
          let xformminus1 = y => xform(y) - 1;
          min = ds.fullData.reduce((ymin, el) => Math.min(ymin, xformminus1(el.y_min)), min);
        }
        if (Number.isFinite(min)) {
          ret.ticks['min'] = Math.floor(min);
        }
      }

      // Get max
      if (notEmpty(this.paramModel['ymax'])) {
        ret.ticks['max'] = Number(this.paramModel['ymax'])
      } else if (this.paramModel['intervals']) {
        // Need to manually calculate max if we have intervals
        let max = -Infinity;
        for (let ds of dataSets) {
          let xform = getDatasetXForm(ds);
          let xformplus1 = y => xform(y) + 1;
          max = ds.fullData.reduce((ymax, el) => Math.max(ymax, xformplus1(el.y_max)), max);
        }
        if (Number.isFinite(max)) {
          ret.ticks['max'] = Math.ceil(max);
        }
      }
      return ret;
    }

    // Pass this nested object to chart.js for rendering
    this.chartOptions = {
      type: this.paramModel['intervals'] ? 'lineWithBars' : 'line',
      data: {
        xLabels: xs,
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
            scaleLabel: {
              display: !!this.paramModel['xlabel'],
              labelString: this.paramModel['xlabel']
            }
          }],
          yAxes: [makeYAxis()]
        },
        display: true,
        maintainAspectRatio: false,
        elements: {
          line: {
            tension: this.paramModel['smoothing'] == 'bezier' ? 0.2 : 0 // disables bezier curves
          }
        },
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
            let dataObject = dataSets[datasetIndex].fullData[index]
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