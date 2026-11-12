import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  items: [],
}

const applicationsSlice = createSlice({
  name: 'applications',
  initialState,
  reducers: {
    applicationsLoaded(state, action) {
      state.items = action.payload
    },
    applicationAdded(state, action) {
      state.items.unshift(action.payload)
    },
    applicationUpdated(state, action) {
      const index = state.items.findIndex((application) => application.id === action.payload.id)
      if (index >= 0) state.items[index] = action.payload
    },
  },
})

export const { applicationsLoaded, applicationAdded, applicationUpdated } = applicationsSlice.actions
export const selectApplications = (state) => state.applications.items
export default applicationsSlice.reducer
