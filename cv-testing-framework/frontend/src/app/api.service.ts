import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  baseurl = "";// same domain and port as frontend
  httpHeaders = new HttpHeaders({'Content-Type': 'application/json'});
  options = { headers: this.httpHeaders, withCredentials: true };
  externalOptions = { headers: this.httpHeaders, withCredentials: false };

  constructor(private http: HttpClient) { }

  // raw API request
  rawpost(fragment: string, data: any): Observable<any> {
      return this.http.post(this.baseurl + fragment, data, this.options);
  }

  // raw API request
  rawget(fragment: string): Observable<any> {
      return this.http.get(this.baseurl + fragment, this.options);
  }

  // raw API request
  externalPost(url: string, data: any): Observable<any> {
      return this.http.post(url, data, this.externalOptions);
  }

  // raw API request
  externalGet(url: string): Observable<any> {
      return this.http.get(url, this.externalOptions);
  }

  // login
  login(username: string, password: string): Observable<any> {
    return this.http.post(this.baseurl + '/api/auth/login',
        {username: username, password: password}, this.options);
  }

    // Get the login status
  loginStatus(): Observable<any> {
      return this.http.post(this.baseurl + '/api/auth/status', {}, this.options);
  }

    // Get running jobs on VRL
  getVRLRunningJobs(): Observable<any> {
      return this.http.get(this.baseurl + '/api/monitors/runningvrljobs', {});
  }
  
  logout(): Observable<any> {
    return this.http.post(this.baseurl + '/api/auth/logout', {}, this.options);
  }

  // gets test packages to display on VRL form
  getAllTestPackages(): Observable<any> {
    return this.http.get(this.baseurl + '/testpackages', this.options);
  }

  /**
   * Get graph data for a given group type
   */
  getGraphData(id: string): Observable<any> {
      return this.http.get(this.baseurl + '/api/results/testname/' + id, this.options);
  }

  /**
   * send VRL form data to back-end as post request
   * @returns http response
   */
  submitVRLTest(data): Observable<any> {
      return this.http.post(this.baseurl + '/api/vrlsubmit/submit', data, this.options);
  }

  /**
   * send triage form data to back-end as post request
   * @returns http response
   */
  submitTriageTest(data): Observable<any> {
    return this.http.post(this.baseurl + '/dispatch', data);
  }

  /**
   * get response from submitting VRL test
   * @returns http response
   */
  getJSONResponse(): Observable<any> {
    return this.http.get(this.baseurl + '/dispatch');
  }

  /**
   * retrieves full database to display on front-end
   * @returns http response
   */
  getDBResponse(): Observable<any> {
    return this.http.get(this.baseurl + '/senddb');
  }

  /**
   * retrieve all logs based on selected task ID to display on front-end
   * @param taskId, the task ID selected to display logs of
   * @returns http response
   */
  getLogs(taskId:string): Observable<any> {
    let params = new HttpParams();
    params = params.append('taskId', taskId);
    return this.http.get(this.baseurl + '/logs', {params: params, withCredentials: true});
  }

  /**
   * queries back-end to get available options for next input field in the triage form
   * @param field, the type of data needed to be retrieved (ie. changelists, test suites)
   * @param item, what the user selected
   * @returns http response
   */
  triageQuery(field:string, item:string): Observable<any> {
    let params = new HttpParams();
    params = params.append('field', field);
    params = params.append('item', item);
    return this.http.get(this.baseurl + '/triage', {params: params});
  }

  /**
   * Gets one vrl job details by api provided by django framework
   * @param serial the serial number of the selected vrl job
   * @returns the vrl job info in JSON
   */
  getOneJob(serial): Observable<any>{
      return this.http.get(this.baseurl + '/api/dvsvrl/jobs/' + serial, this.options);
  }

  /**
   * Gets group list
   * @returns group list
   */
  getGroupList(): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/gg2groups', this.options);
}

  /**
   * Gets one group after click one group in the group list
   * @param id
   * @returns one group
   */
  getOneGroup(id): Observable<any>{
      return this.http.get(this.baseurl + '/api/dvsvrl/gg2groups/' + id, this.options);
  }

  /**
   * Gets gg2 job with the certain id after the clicking one gg2 job dates
   * @param id the id of the gg2 job
   * @returns gg2 job returned by django api, in JSON form
   */
  getGg2Job(id): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/gg2jobs/' + id, this.options);
  }

  /**
   * Gets builds, get the builds info from the backend
   * @returns builds
   */
  getBranches(): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/builds', this.options);
  }
  
  /**
   * This function will query for details required to filter the packages
   * such as build types, os, branches etc
   */
  getDvsPackageFilters(): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvs/getpackagemetadata/', this.options)
  }


  /**
   * Gets build pkgs in JSON with user speicifed parameters, listed below
   * @param branch branch selected by user
   * @param build build selected by user
   * @param buildType buildType selected by user
   * @returns build pkgs
   */
  getBuildPkgs(branch: string, build: string, buildType: string):Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/buildspkg/' + branch + "/" +  build + "/" + buildType, this.options);
  }

  /**
   * Gets machine pools in JSON
   * @returns machine pools
   */
  getMachinePools(): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/machine_pools', this.options);
  }

  /**
   * Gets machines the machines info, include but not limited to, Operating System, CPU, GPU, etc.
   * @returns machines info in JSON
   */
  getMachines(): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/machines', this.options);
  }

  /**
   * Gets machines by single test id
   * @param testId
   * @returns id of the single test
   */
  getMachinesByTestId(testId): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/machines' + '/' + testId,  {headers: this.httpHeaders});
  }


  /**
   * Gets tests the test info
   * @returns tests info in JSON
   */
  getTests(): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/tests', this.options);
  }
  
  /**
   * Submits a vrl job to local database
   * @param JSONdata 
   * @returns vrl job 
   */
  submitVrlJob(JSONdata): Observable<any>{
    return this.http.post(this.baseurl + '/api/dvsvrl/jobs', JSONdata, {headers: this.httpHeaders});
  }
  
  /**
   * Gets submitted vrl from the local database
   * @returns submitted vrl 
   */
  getSubmittedVrl(): Observable<any>{
    return this.http.get(this.baseurl + '/api/dvsvrl/vrlSubmittedJobs',  {headers: this.httpHeaders});
  }
  
  /**
   * Gets machine from machine pool, i.e. further filtering the machine with the selected machine pool
   * @param machinePoolId 
   * @returns machine from machine pool 
   */
  getMachineFromMachinePool(machinePoolId): Observable<any>{

    return this.http.get(this.baseurl + '/api/dvsvrl/machines/machine_pools/' + machinePoolId,  {headers: this.httpHeaders});
  }

  /**
   * Gets machine monitoring data
   * @returns machine monitoring data 
   */
  getMachineMonitoringData(days, filter): Observable<any>{
    return this.http.get(this.baseurl + '/api/mm/'+days+'/'+filter,  {headers: this.httpHeaders});
  }
  
  /**
   * Gets all the teams info
   * @returns list of teams and its id 
   */
  getAllTeams(): Observable<any>{
    return this.http.get(this.baseurl + '/api/ops/getallteams',  {headers: this.httpHeaders});
  }

  /**
   * Gets ops information for the team
   * @returns list of teams and its id 
   */
  getOpsByTeam(team): Observable<any>{
    return this.http.get(this.baseurl + '/api/ops/' + team,  {headers: this.httpHeaders});
  }

  /**
   * Gets bugs based on keywords by team
   * @returns list of bugs 
   */
  getBugsByKeyword(team, days): Observable<any>{
    return this.http.get(this.baseurl + '/api/nvbugs/with-keywords/' + team + '?RequestDateWithin='+days,  {headers: this.httpHeaders});
  }

  /**
   * Gets bugs based on team member
   * @returns list of bugs
   */
  getBugsByMembers(team, days): Observable<any>{
    return this.http.get(this.baseurl + '/api/nvbugs/without-keywords/' + team + '?RequestDateWithin='+days,  {headers: this.httpHeaders});
  }

  /**
   * Gets all the user added bugs based on the team
   * @returns list of bugs
   */
  getUserAddedBugs(team): Observable<any>{
    return this.http.get(this.baseurl + '/api/nvbugs/get_user_added_bugs/' + team,  {headers: this.httpHeaders});
  }

  /**
   * Add bug to hub db
   */
  add_bug_to_hub(bugid: number, team: string): Observable<any> {
    return this.http.post(this.baseurl + '/api/nvbugs/add_bug/',
        {bugid: bugid, team: team}, this.options);
  }

  /**
   * Delete bug to hub db
   */
  delete_bug_from_hub(bugid: number, team: string): Observable<any> {
    return this.http.post(this.baseurl + '/api/nvbugs/remove_bug/',
        {bugid: bugid, team: team}, this.options);
  }

  /**
   * Gets machine monitoring data
   * @returns machine monitoring data 
   */
  getMachinePoolData(): Observable<any>{
    return this.http.get(this.baseurl + '/api/mm/machinepools',  {headers: this.httpHeaders});
  }

  getPackageUrl(package_name: string, changelist: string): Observable<any> {
    return this.http.get(this.baseurl + '/api/dvs/get_package_url/' + package_name + '/' + changelist)
  }
}
