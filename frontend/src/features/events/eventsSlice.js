import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  events: [],
  registrations: [],
  selectedEvent: null,
}

const eventsSlice = createSlice({
  name: 'events',
  initialState,
  reducers: {
    eventsLoaded(state, action) {
      state.events = action.payload
    },
    registrationsLoaded(state, action) {
      state.registrations = action.payload
    },
    selectedEventChanged(state, action) {
      state.selectedEvent = action.payload
    },
  },
})

export const { eventsLoaded, registrationsLoaded, selectedEventChanged } = eventsSlice.actions
export const selectEvents = (state) => state.events.events
export const selectRegistrations = (state) => state.events.registrations
export const selectSelectedEvent = (state) => state.events.selectedEvent
export default eventsSlice.reducer
