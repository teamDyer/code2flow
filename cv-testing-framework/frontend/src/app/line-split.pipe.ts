import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'lineSplit'
})
export class LineSplitPipe implements PipeTransform {

  transform(value: any, args?: any): any {
      return value.split("\n");
  }

}
