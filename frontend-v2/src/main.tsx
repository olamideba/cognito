import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

declare global {
  interface Window {
    VANTA: any;
  }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.VANTA && window.VANTA.TOPOLOGY) {
        window.VANTA.TOPOLOGY({
            el: '#vanta-bg',
            mouseControls: true,
            touchControls: true,
            gyroControls: false,
            minHeight: 200.00,
            minWidth: 200.00,
            scale: 1.00,
            scaleMobile: 1.00,
            color: 0x000000,
            backgroundColor: 0xffffff
        });
    }
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
