import { Component, OnInit, ElementRef, Input, Output, EventEmitter, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

export interface Point {
  x: number;
  y: number;
}

interface KVPair {
  key: string;
  value: any;
}

@Component({
  selector: 'app-graph-point-inspector',
  templateUrl: './graph-point-inspector.component.html',
  styleUrls: ['./graph-point-inspector.component.css']
})
export class GraphPointInspectorComponent implements OnInit {

  system: string;
  test: string;
  kvs: Array<KVPair> = [];

  @ViewChild("mainEl", { static: true })
  mainEl: ElementRef;

  // Toggle visibility
  @Input() showPoint: boolean = true;
  @Output() shouldHide = new EventEmitter<boolean>();

  // Calculated measurements
  goRight: boolean = true;
  goUp: boolean = false;

  // Manual positioning
  doingMeasurement: boolean = false;
  x: number = 0;
  y: number = 0;
  ox: number = 0;
  oy: number = 0;
  @Input() set position(p: Point) {
    let didMove = false;
    if (p.x != this.x || p.y != this.y) {
      didMove = true;
    }
    // Set values to defaults to do measurement
    this.x = 0;
    this.y = 0;
    this.goRight = true;
    this.goUp = false;
    this.ox = 0;
    this.oy = 0;
    this.doingMeasurement = true;
    if (didMove) {
      // wait for layout. After layout, we can measure the box and set offsets.
      window.setTimeout(() => {
        this.x = p.x;
        this.y = p.y;
        this.doingMeasurement = false;
        let rect = this.mainEl.nativeElement.getBoundingClientRect();
        let h = rect.height;
        let w = rect.width;
        let topBleed = p.y < h;
        let bottomBleed = p.y + h > window.innerHeight;
        let goUp = bottomBleed && !topBleed;
        let goRight = p.x < window.innerWidth / 2;
        this.goRight = goRight;
        this.goUp = goUp;
        this.ox = this.goRight ? 0 : -w;
        this.oy = bottomBleed ? (topBleed ? -h / 2 : -h) : 0;
        // Nice layout may have failed, so just jam box inside view to prevent scroll
        if (this.ox + this.x < 0) { this.ox = -this.x; }
        if (this.ox + this.x + w > window.innerWidth) { this.ox = window.innerWidth - this.x - w; }
        if (this.oy + this.y < 0) { this.oy = -this.y; }
        if (this.oy + this.y + h > window.innerHeight) { this.oy = window.innerHeight - this.y - h; }
      }, 0);
    }
  }

  constructor(private route: ActivatedRoute) { }

  setModel(model: object) {
    this.kvs = [];
    for (let key of Object.keys(model)) {
      let val = model[key]
      this.kvs.push({
        key: key,
        value: val
      });
    }
  }

  hide() {
    this.shouldHide.emit(true);
  }

  getValues(jsonstr: string) {
    return jsonstr;
  }

  ngOnInit() {
    this.route.paramMap.subscribe(pmap => {
      this.system = pmap.get('testSystem');
      this.test = pmap.get('testName');
    })
  }

}
