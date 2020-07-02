// Utilities for working with chartjs.

// Point for chart.js
export interface Point {
    x: number;
    y: number;
}

// Interface for a data set in charts (subset)
export interface DataSet {
    fill?: boolean;
    label: string;
    data: Array<Point>;
    fullData: Array<any>;
    borderColor?: string;
    pointRadius?: number;
    pointHoverRadius?: number;
    pointHitRadius?: number;
    geomean?: number;
    geostddev?: number;
    params?: object;
    hidden?: boolean;
}

// Get all of the unique values in arr into an array. For example, if we had
// an array of test results, and each result had a changelist, we could extract
// all of the unqiue changelists into a new array (sorted).
export function getUnique<T, U>(arr: Array<T>, f: ((_: T) => U)): Array<U> {
    let uset = new Set(arr.map(f));
    return Array.from(uset.keys()).sort();
}

// Get all of the unique values in arr into an array, but where each item
// can have multiple items. For example, if we had
// an array of test results, and each result had a set of subtests, we could extract
// all of the unqiue subtest names into a new array (sorted).
export function getUniqueMapcat<T, U>(arr: Array<T>, f: ((_: T) => Array<U>)): Array<U> {
    let uset: Set<U> = new Set();
    for (let x of arr) {
        let subarr = f(x)
        for (let y of subarr) {
            uset.add(y);
        }
    }
    return Array.from(uset.keys()).sort();
}

// Get geomean. Uses an approximation to handle 0s and negative numbers gracefully
// by splitting the values into positives and negative subsets.
export function geoMean(arr: Array<number>): number {
    let pos = arr.filter(x => x > 0);
    let neg = arr.filter(x => x < 0);
    let gplus = pos.reduce((accum, x) => accum += Math.log(x), 0) / pos.length;
    let gminus = neg.reduce((accum, x) => accum += Math.log(-x), 0) / neg.length;
    let mean = 0;
    if (pos.length) {
        mean += Math.exp(gplus) * (pos.length / arr.length);
    }
    if (neg.length) {
        mean -= Math.exp(gminus) * (neg.length / arr.length);
    }
    return mean;
}

export function diffPercent(from: number, x: number) {
    return 100 * Math.round(1e4 * ((x - from) / from)) / 1e4;
}

// Actually geometric zscore
// https://en.wikipedia.org/wiki/Geometric_standard_deviation#Geometric_standard_score
// Also correct for dividie by zero in case of constant dataset (0 stddev).
export function zScore(u: number, sigma: number, x: number) {
    const lsig = Math.log(sigma);
    return lsig == 0 ? 0 : (Math.log(x) - Math.log(u)) / lsig;
}

// Transform an array of points into an array of deltas from the geoMean
// Good for graphing
export function geoMeanPoints(points: Array<Point>): Array<Point> {
    let mean = geoMean(points.map(p => p.y));
    let ret = [];
    for (let i = 0; i < points.length; i++) {
        ret[i] = {
            x: points[i].x,
            y: diffPercent(mean, points[i].y)
        }
    }
    return ret;
}

// Get the geometric standard deviation of an array.
// Takes a pre-computed geomean as well. Calculation taken from definition
// of geometric stddeviation.
// https://en.wikipedia.org/wiki/Geometric_standard_deviation
export function geoStdDev(ys: Array<number>, geomean: number) {
    let innerSum = 0;
    if (ys.length == 0) {
        return 1; // Avoid NaNs.
    }
    for (let y of ys) {
        innerSum += Math.pow(Math.log(y / geomean), 2);
    }
    let expo = Math.sqrt(innerSum / ys.length);
    return Math.exp(expo);
}

// Transform an array of points into an array of zscores.
// Good for graphing
export function zScorePoints(points: Array<Point>): Array<Point> {
    let ys = points.map(p => p.y);
    let mean = geoMean(ys);
    let stddev = geoStdDev(ys, mean);
    let ret = [];
    for (let i = 0; i < points.length; i++) {
        ret[i] = {
            x: points[i].x,
            y: zScore(mean, stddev, points[i].y)
        }
    }
    return ret;
}

// Generate colors for graphs.
export function colorForLabel(label): string {
    // Hash label, then convert to color. This keeps colors stable
    // when switching through multiple graphs with the same labels.
    // Use djb's simple hash function with rounds so things like
    // gm200 and gm204 are very different colors.
    let hash = 3412431;
    for (let round = 0; round < 4; round++) {
        for (let i = 0; i < label.length; i++) {
            let x = label.charCodeAt(i);
            hash = ((hash << 5) - hash) + x;
            hash = hash & hash; // convert to 32 bit integer
        }
        hash = ((hash << 5) - hash) + 123;
    }
    return '#' + (hash.toString(16) + '0000000').slice(2, 8); 
}

// Get point data for a graph that will be passed to Chart.js
export function makeDataset(points: Array<Point>, label: string, fullData: Array<any>, params = {}): DataSet {
    let ys = fullData.map(el => el.y);
    let gm = geoMean(ys);
    return {
        fill: false,
        label: label,
        data: points,
        borderColor: colorForLabel(label),
        fullData: fullData,
        pointHoverRadius: params['hide_points'] ?  0 : 6,
        pointRadius: params['hide_points'] ? 0 : 6,
        pointHitRadius: 6,
        geomean: gm,
        geostddev: geoStdDev(ys, gm),
        params: params
    };
}