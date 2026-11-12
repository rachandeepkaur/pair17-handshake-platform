import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  companies: [],
  jobs: [],
  selectedCompany: null,
  selectedJob: null,
}

const jobsCompaniesSlice = createSlice({
  name: 'jobsCompanies',
  initialState,
  reducers: {
    companiesLoaded(state, action) {
      state.companies = action.payload
    },
    jobsLoaded(state, action) {
      state.jobs = action.payload
    },
    selectedCompanyChanged(state, action) {
      state.selectedCompany = action.payload
    },
    selectedJobChanged(state, action) {
      state.selectedJob = action.payload
    },
  },
})

export const { companiesLoaded, jobsLoaded, selectedCompanyChanged, selectedJobChanged } = jobsCompaniesSlice.actions
export const selectCompanies = (state) => state.jobsCompanies.companies
export const selectJobs = (state) => state.jobsCompanies.jobs
export const selectSelectedCompany = (state) => state.jobsCompanies.selectedCompany
export const selectSelectedJob = (state) => state.jobsCompanies.selectedJob
export default jobsCompaniesSlice.reducer
