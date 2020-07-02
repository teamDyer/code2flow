import { Component, OnInit, Input } from '@angular/core';
import { FormGroup } from '@angular/forms';
import { ApiService } from 'src/app/api.service';

const DVS_BINARY_DROP_URL = "/api/dvs/binarydrop"
@Component({
  selector: 'app-dvs-unit',
  templateUrl: './dvs-unit.component.html',
  styleUrls: ['./dvs-unit.component.css']
})

export class DvsUnitComponent implements OnInit {
  @Input() parentForm: FormGroup
  
  err: string = null;
  branchList: {}
  buildList: {}
  operatingSystemList: {}
  sourceList: {}
  packageList: {}
  isolation_modes: {}
  changeList:  any[]
  emptySelection: {}
  available_cls: any[]

  constructor(public api: ApiService) { 
    this.packageList = [{"name": "None"}];
    this.changeList = [{"changelist": "None"}];
  }

  ngOnInit() {    
    this.api.getDvsPackageFilters()
    .subscribe(
      res =>{
        console.log(res);
        this.branchList = this.getListFromMap(res['branch']);
        this.buildList = this.getListFromMap(res['build']);
        this.operatingSystemList = this.getListFromMap(res['os']);
        this.sourceList = this.getListFromMap(res['source']);
        this.isolation_modes = this.getListFromMap(res['isolation_modes']);
        if(res['default'] && res['default']["isolation_mode"])
          this.parentForm.patchValue({
            isolation_mode: res['default']["isolation_mode"]
          }) //Default isolation mode
      },
      err => {
        console.log(err)
        this.err = err;
      }
    );
  }

  getListFromMap(map){
    let list =  []
    for(let key in map){
      list.push({key: map[key], value: key})
    }
    return list
  }

  filterPackageList(){
    let formData = this.parentForm.getRawValue()
    let branch = formData.package_branch
    let build = formData.package_build
    let os = formData.operatingSystem
    if(branch == null || build == null || os == null) return
    os = os.key
    this.api.rawget(DVS_BINARY_DROP_URL + "/all_builds/" + branch + "+" + build + "+"+os)
    .subscribe(
      res =>{
        if(res.length > 0){
          this.packageList = res
        }
      },
      err => {
        console.log(err)
        this.err = err;
      }
    );
  }

  filterChangeList(){
    let formData = this.parentForm.getRawValue()
    let package_name = formData.package_name
    if(package_name == null) return
    this.api.rawget(DVS_BINARY_DROP_URL + "/changelists/" + package_name)
    .subscribe(
      res =>{
        if(res.length > 0){
          this.changeList = res.sort(function(a, b){
            return parseFloat(a.changelist) - parseFloat(b.changelist)
          })
        }
      },
      err => {
        console.log(err)
        this.err = err;
      }
    );
  }

  getAvailableChangelists(){    
    return this.available_cls
  }

  updateAvailableCls(){
    let formData = this.parentForm.getRawValue()
    let first_changelist = formData.first_changelist
    let last_changelist = formData.last_changelist
    this.available_cls =  this.changeList.filter(function(cl) {      
      let changelist = parseFloat(cl.changelist)
      return parseFloat(first_changelist) <= changelist && changelist <= parseFloat(last_changelist)
    });
    this.setPackageUrls()
  }

  setPackageUrls(){
    let formData = this.parentForm.getRawValue()
    let isolation_mode = formData.isolation_mode
    let changelist = formData.package_changelist
    let first_changelist = formData.first_changelist
    let last_changelist = formData.last_changelist
    let changelistArray = []
    if(isolation_mode == "BRS" || isolation_mode == "SIS"){
      if(first_changelist == null || last_changelist == null) return
      changelistArray.push(first_changelist)
      if(isolation_mode == "SIS" && formData.selected_changelists != null )
        changelistArray = changelistArray.concat(formData.selected_changelists)
      changelistArray.push(last_changelist)
    }else{
      if(changelist == null ) return
      changelistArray.push(changelist)
    }
    let package_name = formData.package_name
    let notFoundCls = []
    for(let i in changelistArray){
      let cl = changelistArray[i]
      if(cl == 'None') continue
      this.api.getPackageUrl(package_name, cl)
      .subscribe(
        res =>{
          let package_urls = this.parentForm.getRawValue().package_urls
          if(package_urls == null)
            package_urls = {}
          package_urls[cl] = res.package_url
          this.parentForm.patchValue({
            package_urls: package_urls
          })
        },
        err => {
          console.log(err)
          notFoundCls.push(cl)
          this.err = err.statusText;
          if(err.error.trim() == "DOESNT_EXIST")
            this.err = "Package URLs not found for " + notFoundCls.join(', ')
        }
      );
    }
  }
    
}
