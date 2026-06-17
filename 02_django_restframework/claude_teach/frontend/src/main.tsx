import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { store } from './app/store'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Provider : 全コンポーネントから Store にアクセスできるようにする */}
    <Provider store={store}>
      {/* BrowserRouter : URLベースのルーティングを有効にする */}
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Provider>
  </StrictMode>,
)
