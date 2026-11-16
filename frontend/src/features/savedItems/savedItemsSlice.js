import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  events: [],
  jobs: [],
}

const savedItemsSlice = createSlice({
  name: 'savedItems',
  initialState,
  reducers: {
    savedEventsLoaded(state, action) {
      state.events = action.payload
    },
    savedJobsLoaded(state, action) {
      state.jobs = action.payload
    },
  },
})

export const { savedEventsLoaded, savedJobsLoaded } = savedItemsSlice.actions
export const selectSavedEvents = (state) => state.savedItems.events
export const selectSavedJobs = (state) => state.savedItems.jobs
export default savedItemsSlice.reducer
