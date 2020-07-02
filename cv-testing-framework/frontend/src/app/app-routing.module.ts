import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { SubmitJobComponent } from './submit-job/submit-job.component';
import { SubmitVrlJobComponent } from './submit-vrl-job/submit-vrl-job.component';
import { MonitorJobComponent } from './monitor-job/monitor-job.component';
import { NotfoundComponent } from './notfound/notfound.component';
import { LoginComponent } from './login/login.component';
import { ApiviewComponent } from './apiview/apiview.component';
import { JobComponent } from './job/job.component';
import { VisualizerComponent } from './visualizer/visualizer.component';
import { OpsComponent } from './ops/ops.component';
import { MachineMonitoringComponent } from './machine-monitoring/machine-monitoring.component';
import { NvbugsComponent } from './nvbugs/nvbugs.component';
import { SuiteWizardComponent } from './suite-wizard/suite-wizard.component';
import { SatelliteUiComponent } from './satellite-ui/satellite-ui.component';

const routes: Routes = [
    { path: 'login', component: LoginComponent },
    { path: "httpview", component: ApiviewComponent },
    { path: 'home', component: HomeComponent },
    { path: 'submit-job', component: SubmitJobComponent },
    { path: 'submit-vrl-job', component: SubmitVrlJobComponent },
    { path: 'monitor-job', component: MonitorJobComponent },

    // path for active ops and open bugs
    { path: 'ops', component: OpsComponent },
    { path: 'ops/deletebug', component: OpsComponent },
    { path: 'nvbugs', component: NvbugsComponent },

    // path for machine monitoring stats
    { path: 'mm', component: MachineMonitoringComponent },
    
    // See an individual job
    { path: "job/:testSystem/:testName/:rowid", component: JobComponent },

    // Visualization routes
    { path: "view/:testSystem/:testName/:query/:renderer", component: VisualizerComponent },
    { path: "view/:testSystem/:testName/:query", component: VisualizerComponent },
    { path: "view/:testSystem/:testName", component: VisualizerComponent },
    {
        path: '',
        redirectTo: '/home',
        pathMatch: 'full'
    },

    // Satellite UI
    { path: 'satellite', component: SatelliteUiComponent },
    { path: 'satellite/:satellite', component: SatelliteUiComponent },
    { path: 'satellite/:satellite/:subpage', component: SatelliteUiComponent },
    { path: 'satellite/:satellite/:subpage/:itemid', component: SatelliteUiComponent },

    // Suite Wizard
    { path: 'wizard', component: SuiteWizardComponent },

    // Default (not found)
    { path: '**', component: NotfoundComponent },
];

@NgModule({
    imports: [RouterModule.forRoot(routes)],
    exports: [RouterModule]
})
export class AppRoutingModule { }
