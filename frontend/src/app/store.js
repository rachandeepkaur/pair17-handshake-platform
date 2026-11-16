import { configureStore } from '@reduxjs/toolkit'
import applicationsReducer from '../features/applications/applicationsSlice'
import assistantReducer from '../features/assistant/assistantSlice'
import authReducer from '../features/auth/authSlice'
import eventsReducer from '../features/events/eventsSlice'
import jobsCompaniesReducer from '../features/jobsCompanies/jobsCompaniesSlice'
import savedItemsReducer from '../features/savedItems/savedItemsSlice'

export const store = configureStore({
  reducer: {
    applications: applicationsReducer,
    assistant: assistantReducer,
    auth: authReducer,
    events: eventsReducer,
    jobsCompanies: jobsCompaniesReducer,
    savedItems: savedItemsReducer,
  },
})
