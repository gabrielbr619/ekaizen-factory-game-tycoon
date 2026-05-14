import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { createResilientApi } from './api'
import './style.css'

const root = createRoot(document.getElementById('app') ?? document.body)

root.render(
  <StrictMode>
    <App api={createResilientApi()} />
  </StrictMode>,
)
