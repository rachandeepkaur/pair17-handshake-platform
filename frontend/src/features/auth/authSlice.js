import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  token: localStorage.getItem('token'),
  role: localStorage.getItem('role'),
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    sessionStarted(state, action) {
      state.token = action.payload.access_token
      state.role = action.payload.role
    },
    sessionCleared(state) {
      state.token = null
      state.role = null
    },
  },
})

export const { sessionStarted, sessionCleared } = authSlice.actions
export const selectToken = (state) => state.auth.token
export const selectRole = (state) => state.auth.role
export const selectIsAuthenticated = (state) => Boolean(state.auth.token)
export default authSlice.reducer
