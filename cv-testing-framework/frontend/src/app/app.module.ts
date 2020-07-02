import { BrowserModule } from '@angular/platform-browser';
import { NgModule, ErrorHandler } from '@angular/core';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent, GlobalErrorHandler } from './app.component';
import { HomeComponent } from './home/home.component';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatRadioModule } from '@angular/material/radio';
import { MatCardModule } from '@angular/material/card';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatDialogModule } from '@angular/material/dialog';
import { MatTabsModule } from '@angular/material/tabs';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material';
import { MatSortModule } from '@angular/material/sort';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatExpansionModule } from '@angular/material/expansion';
import {MatIconModule} from '@angular/material/icon';
import {MatTooltipModule} from '@angular/material/tooltip';

import { BannerComponent } from './banner/banner.component';
import { MatListModule } from '@angular/material/list';
import { SpinnerComponent } from './spinner/spinner.component';
import { SubmitJobComponent } from './submit-job/submit-job.component';
import { SubmitVrlJobComponent } from './submit-vrl-job/submit-vrl-job.component';
import { MonitorJobComponent } from './monitor-job/monitor-job.component';
import { AutoRefreshComponent } from './auto-refresh/auto-refresh.component';
import { NotfoundComponent } from './notfound/notfound.component';
import { CachingInterceptor } from './caching-interceptor.service';
import { RequestCache } from './request-cache.service';
import { InlineFileComponent } from './inline-file/inline-file.component';
import { LoginComponent } from './login/login.component';
import { ApiviewComponent } from './apiview/apiview.component';
import { JobComponent } from './job/job.component';
import { VisualizerComponent } from './visualizer/visualizer.component';
import { DenseTableComponent } from './dense-table/dense-table.component';
import { LineGraphComponent } from './line-graph/line-graph.component';
import { ParamChooserComponent } from './param-chooser/param-chooser.component';
import { GraphPointInspectorComponent } from './graph-point-inspector/graph-point-inspector.component';
import { LineSplitPipe } from './line-split.pipe';
import { NvbugsComponent } from './nvbugs/nvbugs.component';
import { OpsComponent } from './ops/ops.component';
import { MachineMonitoringComponent } from './machine-monitoring/machine-monitoring.component';
import { LinegComponent } from './lineg/lineg.component';
import { DenseTableCellComponent } from './dense-table-cell/dense-table-cell.component';
import { SuiteWizardComponent } from './suite-wizard/suite-wizard.component';
import { BarChartComponent } from './bar-chart/bar-chart.component';
import { PieChartComponent } from './pie-chart/pie-chart.component';
import { ExportcsvComponent } from './exportcsv/exportcsv.component';
import { UnitUnderTestComponent } from './unit-under-test/unit-under-test.component';
import { DvsUnitComponent } from './unit-under-test/dvs-unit/dvs-unit.component';
import { SatelliteUiComponent } from './satellite-ui/satellite-ui.component';

@NgModule({
    declarations: [
        AppComponent,
        HomeComponent,
        BannerComponent,
        SpinnerComponent,
        SubmitJobComponent,
        SubmitVrlJobComponent,
        MonitorJobComponent,
        AutoRefreshComponent,
        NotfoundComponent,
        InlineFileComponent,
        LoginComponent,
        ApiviewComponent,
        JobComponent,
        VisualizerComponent,
        DenseTableComponent,
        LineGraphComponent,
        ParamChooserComponent,
        GraphPointInspectorComponent,
        LineSplitPipe,
        NvbugsComponent,
        OpsComponent,
        MachineMonitoringComponent,
        LinegComponent,
        DenseTableCellComponent,
        SuiteWizardComponent,
        BarChartComponent,
        PieChartComponent,
        ExportcsvComponent,
        UnitUnderTestComponent,
        DvsUnitComponent,
        SatelliteUiComponent,
    ],
    imports: [
        BrowserModule,
        HttpClientModule,
        AppRoutingModule,
        NgbModule,
        BrowserAnimationsModule,
        MatButtonModule,
        MatSelectModule,
        MatCheckboxModule,
        MatRadioModule,
        MatTooltipModule,
        MatCardModule,
        FormsModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatTabsModule,
        MatInputModule,
        MatTableModule,
        MatListModule,
        MatSortModule,
        MatPaginatorModule,
        MatSnackBarModule,
        MatExpansionModule,
        MatIconModule,
        MatTooltipModule
    ],
    providers: [
        RequestCache,
        {provide: HTTP_INTERCEPTORS, useClass: CachingInterceptor, multi: true},
        {provide: ErrorHandler, useClass: GlobalErrorHandler}
    ],
    bootstrap: [AppComponent]
})
export class AppModule { }
