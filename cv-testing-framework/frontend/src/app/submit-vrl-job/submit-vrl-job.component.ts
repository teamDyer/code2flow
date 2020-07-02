import { Component, OnInit, Input } from '@angular/core';
import { ApiService } from '../api.service';
import { FormGroup } from '@angular/forms';
import { MatRadioChange} from '@angular/material';

const DVS_URL = "/api/dvs"

@Component({
    selector: 'app-submit-vrl-job',
    templateUrl: './submit-vrl-job.component.html',
    styleUrls: ['./submit-vrl-job.component.css']
})
export class SubmitVrlJobComponent implements OnInit {
    @Input() parentForm: FormGroup

    err: string = null;
    waitingForMachineConfigQuery: boolean = false;
    waitingForTestNameQuery: boolean = false;
    test_system: string;
    test_systems: string[] = ['VRL'];
    default_test_name_String: string = "-- Select Test System to get list of test names --";
    no_test_name_String: string = "-- No test(s) found for selected UUT parameter and test system --";
    default_gpu_String: string = "-- Select Test Name to get list of GPUs --";
    no_gpu_String: string = "-- No GPUs found for selected test name(s) --";
    default_machine_name_String: string = "-- Select Test Name to get list of Machines --";
    no_machine_name_String: string = "-- No Machine(s) found for selected test name(s) --";
    test_names: string[] = [];
    gpu_names: string[] = [];
    machinepool_names: string[] = [];
    machine_names: string[] = [];
    selectedTestNames: string[] = [];
    deselectGPUType: boolean = true;
    deselectMachineType: boolean = true;
    show_placeholder_for_testnames: boolean = true;
    show_placeholder_for_machineconfig: boolean = true;
    no_machine_config_found: boolean = false;
    no_test_name_found: boolean = false;

    constructor(public api: ApiService){
    }


    ngOnInit() {
    }

    getTestSystemDetails(){

        let formData = this.parentForm.getRawValue()

        if( formData.test_system === 'VRL'){
            this.test_system = formData.test_system;
            let package_name = formData.package_name;

            this.waitingForTestNameQuery = true;
            this.api.rawget(DVS_URL + "/get_package_tests/" + package_name + "/" + this.test_system )
                .subscribe(
                    res => {
                        this.waitingForTestNameQuery = false;
                        this.show_placeholder_for_testnames = false;
                        if (res.length > 0) {
                            this.no_test_name_found = false;
                            this.test_names = res
                        }else{
                            this.no_test_name_found = true;
                        }
                    },
                    err => {
                        console.log(err)
                        this.err = err;
                    }
                );
        } else {
            this.test_names = [];
            this.gpu_names = [];
            this.machine_names = [];
            this.default_test_name_String = "-- Select Test System to get list of test names --";
            this.show_placeholder_for_testnames = true;
            this.no_test_name_found = false;
        }

    }

    radioChange($event: MatRadioChange) {
        console.log($event.source.name, $event.value);
    
        if ($event.source.name === 'radioOptForGPUAndMachineType') {
            if( $event.value === 'gpuType'){
                this.deselectGPUType = false;
                this.deselectMachineType = true;
            } else if( $event.value === 'machineType'){
                this.deselectGPUType = true;
                this.deselectMachineType = false;
            }
        }
    }

    onTestNameSelectionChange(event){
        let formData = this.parentForm.getRawValue();

        if(formData.test_names !== null){
            let selected_test_names = formData.test_names;
            if(selected_test_names.length > 0){                
                this.waitingForMachineConfigQuery = true;
                let test_name_list = "";
                for (let ctr in selected_test_names) {
                    let test_name_with_quote = "'" + selected_test_names[ctr] + "'";
                    test_name_list = test_name_list + test_name_with_quote + "+";
                 }

                this.api.rawget(DVS_URL + "/get_machineconfig_info/" +  test_name_list)
                .subscribe(
                    res_machineconfig => {
                        this.waitingForMachineConfigQuery = false;
                        if (res_machineconfig.length > 0) {
                            this.gpu_names = [];
                            this.machinepool_names = [];
                            this.machine_names = [];
                            this.show_placeholder_for_machineconfig = false;

                            const array = [1,3,2,5,2,1,4,2,1]
                            const newArray = array.filter((elem, i, arr) => {
                            if (arr.indexOf(elem) === i) {
                                return elem
                                }
                            })

                            for (let machineconfig in res_machineconfig){
                                // Only push unique values
                                if (this.gpu_names.indexOf(res_machineconfig[machineconfig].gpuname) == -1) {
                                    this.gpu_names.push(res_machineconfig[machineconfig].gpuname);
                                }

                                if (this.machinepool_names.indexOf(res_machineconfig[machineconfig].machinepoolname) == -1) {
                                    this.machinepool_names.push(res_machineconfig[machineconfig].machinepoolname);
                                }

                                if (this.machine_names.indexOf(res_machineconfig[machineconfig].machinename) == -1) {
                                    this.machine_names.push(res_machineconfig[machineconfig].machinename);
                                }
                            }
                        }else{
                            this.gpu_names = [];
                            this.machinepool_names = [];
                            this.machine_names = [];
                            this.no_machine_config_found = true;
                            this.show_placeholder_for_machineconfig = false;
                        }
                    },
                    err => {
                        this.waitingForMachineConfigQuery = false;
                        console.log(err)
                        this.err = err;
                    }
                );
                [8]
            }else{
                this.gpu_names = [];
                this.machinepool_names = [];
                this.machine_names = [];
                this.show_placeholder_for_machineconfig = true;
                this.no_machine_config_found = false;
            }
        }else{
            this.gpu_names = [];
            this.machinepool_names = [];
            this.machine_names = [];
            this.show_placeholder_for_machineconfig = true;
            this.no_machine_config_found = false;
        }
    }
}
