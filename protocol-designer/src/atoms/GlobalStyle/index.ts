import { createGlobalStyle } from 'styled-components'
import '@fontsource/public-sans'
import '@fontsource/public-sans/600.css'
import '@fontsource/public-sans/700.css'

export const GlobalStyle = createGlobalStyle<{ enableRedesign?: boolean }>`
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: ${props =>
      props.enableRedesign ?? false ? 'Public Sans' : 'Open Sans'}, sans-serif;
  }
`