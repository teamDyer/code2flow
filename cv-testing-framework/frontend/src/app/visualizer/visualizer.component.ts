import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { ActivatedRoute, Router, ParamMap } from '@angular/router';
import { ParameterDescription, makeModelConform } from '../param-chooser/param-chooser.component';

interface CVFTest {
  system: string;
  name: string;
};

@Component({
  selector: 'app-visualizer',
  templateUrl: './visualizer.component.html',
  styleUrls: ['./visualizer.component.css']
})
export class VisualizerComponent implements OnInit {

  // Allow hiding choosers
  expanded: boolean = true;
  hideVisualization: boolean = false;

  // Choose query (view) / test / system
  system: string;
  test: string;
  allTests: CVFTest[] = [];
  selectedTest: CVFTest = {name: null, system: null};
  query: string;

  // Query configuration
  availableQueries: string[] = [];
  queryParams: ParameterDescription[] = [];
  queryParamModel: object = {};
  queryError: string = null;
  queryData: object[] = [];
  waitingForQuery: boolean = false;

  // Rendering
  availableRenderers: string[] = ['line-graph', 'table'];
  renderParams: ParameterDescription[] = [];
  renderParamModel: object = {};
  renderLabels: Array<string> = [];
  renderer: string;

  // Link patterns for certain column names in a table
  tableMapping = {
    'vrl_serial': 'http://dvsweb/DVSWeb/view/content/vrl/job/view.jsf?id=$'
  };

  constructor(private api: ApiService, private route: ActivatedRoute, private router: Router) { }

  // Switch test suite
  traverse(delta: number) {
    let tests = this.allTests;
    let index = tests.findIndex(t => t.name === this.test && t.system === this.system);
    let finalIndex = (index + delta + tests.length) % tests.length;
    this.selectedTest = tests[finalIndex];
    this.refresh();
  }

  // Make chart.js recalculate chart.
  resize() {
    this.hideVisualization = true;
    this.refresh();
    window.setTimeout(() => {
      this.hideVisualization = false;
    }, 0);
  }
  
  // Build the query string for /api/visualize requests from the query param model
  buildQueryString() {
    let kvPairs = [];
    for (let [key, value] of Object.entries(this.queryParamModel)) {
      if (key != null && value != null && value != '') {
        // do some normalization - local dates -> utc dates
        let param = this.queryParams.find((x) => x.name === key);
        if (param && param.type === 'date') {
          let d = new Date(value);
          value = d.getTime() / 1000;
        }
        kvPairs.push(key + '=' + encodeURIComponent(value));
      }
    }
    return kvPairs.join('&');
  }

  // Sync view to the state of the application.
  refresh() {
    this.redirect(false);
  }

  // Make a query to the backend to get data.
  doQuery() {
    this.queryError = null;
    let urlfrag = `/api/visualize/${this.system}/${this.test}/${this.query}?${this.buildQueryString()}`;
    this.waitingForQuery = true;
    return this.api.rawget(urlfrag).subscribe(responseData => {
      this.waitingForQuery = false;
      // prevent some caching that interferes with some change detection.
      this.queryData = [].concat(responseData.data);
    }, err => {
      this.waitingForQuery = false;
      this.queryError = err.error.error;
      this.queryData = [];
    });
  }

  // If we change parameters locally, we want to update the route
  redirect(removeHistory: boolean) {
    // query model
    let q = Object.assign({}, this.queryParamModel);
    // render model
    for (let key of Object.keys(this.renderParamModel)) {
      q['rdr_' + key] = this.renderParamModel[key];
    }
    // shown labels
    for (let i = 0; i < this.renderLabels.length; i++) {
      q['lbl_' + i] = this.renderLabels[i];
    }
    q['show'] = this.expanded ? 'true' : 'false';
    const system = this.selectedTest ? this.selectedTest.system : this.system;
    const name = this.selectedTest ? this.selectedTest.name : this.test;
    this.router.navigate(['view', system, name, this.query, this.renderer],
      {
        replaceUrl: removeHistory,
        queryParams: q
      });
  }

  // User clicked on a chart
  updateRenderLabels(newLabels: Array<string>) {
    this.renderLabels = newLabels;
    this.redirect(false);
  }

  // Given some url parameters, update the state of the page.
  getStateFromURL(umap: ParamMap, pmap: ParamMap) {
    // Sync state with query parameters.
    this.queryParamModel = {};
    this.renderParamModel = {};
    this.renderLabels = [];
    this.expanded = true;
    for (let k of pmap.keys) {
      if (k === 'show') {
        this.expanded = pmap.get('show') === 'true';
      } else if (k.startsWith('lbl_')) {
        this.renderLabels.push(pmap.get(k));
      } else if (k.startsWith('rdr_')) {
        this.renderParamModel[k.slice(4)] = pmap.get(k);
      } else {
        this.queryParamModel[k] = pmap.get(k);
      }
    }

    // Sync state with route parameters
    this.system = umap.get('testSystem');
    this.test = umap.get('testName');
    this.query = umap.get('query') || 'simple';
    this.renderer = umap.get('renderer') || 'table';
    this.selectedTest = this.allTests.find(t => t.name === this.test && t.system === this.system);

    // Get available parameters for current query from backend, and make sure that the model conforms to this.
    this.api.rawget(`/api/visualize/${this.system}/${this.test}/${this.query}/params?${this.buildQueryString()}`).subscribe(responseData => {
      this.queryParams = responseData.params;
      // Check if model conforms
      if (makeModelConform(this.queryParams, this.queryParamModel)) {
        this.redirect(true);
      }
      this.doQuery();
    });

    // Get all available, alternative queries for the given test suite. 
    this.api.rawget(`/api/visualize/available-queries/${this.system}/${this.test}`).subscribe(x => {
      this.availableQueries = x.map(row => row.query);
      let selectedRow = x.find(row => row.query == this.query)
      this.availableRenderers = selectedRow ? selectedRow.renderers : [];
      if (this.availableRenderers.length == 0) {
        // If no renderers provided, make all available
        this.availableRenderers = ['line-graph', 'table', 'bar-chart', 'pie-chart'];
      }
      // If the current renderer is not available, switch
      let shouldRefresh = false;
      if (this.availableQueries.indexOf(this.query) < 0) {
        this.query = this.availableQueries[0];
        shouldRefresh = true;
      }
      if (this.availableRenderers.indexOf(this.renderer) < 0) {
        this.renderer = this.availableRenderers[0];
        shouldRefresh = true;
      }
      if (shouldRefresh) {
        this.redirect(true);
      }
    });

    // Get renderer parameters
    switch (this.renderer) {
      case 'line-graph':
        this.renderParams = [
          { 'name': 'title', 'type': 'string', 'optional': false, 'doc': 'Set title of displayed graph.' },
          { 'name': 'xlabel', 'type': 'string', 'optional': false, 'doc': 'Set label for the X axis of the graph'},
          { 'name': 'ylabel', 'type': 'string', 'optional': false, 'doc': 'Set label for the Y axis of the graph'},
          { 'name': 'ymin', 'type': 'real', 'optional': true, 'doc': 'Set minimum value for y axis'},
          { 'name': 'ymax', 'type': 'real', 'optional': true, 'doc': 'Set maximum value for y axis'},
          { 'name': 'intervals', 'type': 'boolean', 'optional': false, 'doc': 'Show a box and whisker plot' },
          { 'name': 'hide_points', 'type': 'boolean', 'optional': false, 'doc': 'Hide points on the graph so it does not look cluttered.' },
          {
            'name': 'post',
            'type': 'choice',
            'optional': false,
            'doc': 'Do some post processing on the input data.',
            'options': [
              'none',
              'geomean',
              'zscore'
            ]
          },
          { 'name': 'smoothing', 'type': 'choice', 'optional': false, 'doc': 'Types of line smoothing.', 'options': ['none', 'bezier'] },
          { 'name': 'drop_zeros', 'type': 'boolean', 'optional': false, 'doc': 'Remove points where y=0 from the graph.' },
          { 'name': 'axis_on_right', 'type': 'boolean', 'optional': false, 'doc': 'Put the y axis label on the right of the graph.' }
        ];
        break;
      case 'bar-chart':
        this.renderParams = [
          { 'name': 'title', 'type': 'string', 'optional': false, 'doc': 'Set title of displayed graph.' },
          { 'name': 'xlabel', 'type': 'string', 'optional': false, 'doc': 'Set label for the X axis of the graph'},
          { 'name': 'ylabel', 'type': 'string', 'optional': false, 'doc': 'Set label for the Y axis of the graph'},
          { 'name': 'min', 'type': 'real', 'optional': true, 'doc': 'Minimum value on the value axes (y unless horizontal)' },
          { 'name': 'max', 'type': 'real', 'optional': true, 'doc': 'Maximum value on the value axes (y unless horizontal)' },
          { 'name': 'stacked', 'type': 'boolean', 'optional': false, 'doc': 'Stack bars from different datasets on top of each other.' },
          { 'name': 'horizontal', 'type': 'boolean', 'optional': false, 'doc': 'If checked, layout bars horizontally.' }
        ];
        break;
      case 'pie-chart':
        this.renderParams = [
          { 'name': 'title', 'type': 'string', 'optional': false, 'doc': 'Set title of displayed graph.' },
        ];
        break;
      case 'table':
        this.renderParams = [];
        break;
    }
    makeModelConform(this.renderParams, this.renderParamModel);
  }

  ngOnInit() {
    // Get a list of all available test suites so we can navigate between them.
    this.api.rawget('/api/results/all-tests/all').subscribe((tests: Array<CVFTest>) => {
      this.allTests = tests;
      this.selectedTest = this.allTests.find(t => t.name === this.test && t.system === this.system);
    });

    this.route.paramMap.subscribe(e => {
      let pmap = this.route.snapshot.queryParamMap;
      this.getStateFromURL(e, pmap);
    });

    this.route.queryParamMap.subscribe(e => {
      let umap = this.route.snapshot.paramMap;
      this.getStateFromURL(umap, e);
    });
  }

}
