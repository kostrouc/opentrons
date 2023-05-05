// titled modal page component
import * as React from 'react'

import { TitleBar } from '../structure'
import type { TitleBarProps } from '../structure'
import styles from './modals.css'
import { SpinnerModal } from './SpinnerModal'

// TODO(mc, 2018-06-20): s/titleBar/titleBarProps
export interface SpinnerModalPageProps
  extends React.ComponentProps<typeof SpinnerModal> {
  /** Props for title bar at top of modal page */
  titleBar: TitleBarProps
}

/**
 * Spinner Modal variant with TitleBar
 */
export function SpinnerModalPage(props: SpinnerModalPageProps): JSX.Element {
  const { titleBar, ...spinnerModalProps } = props

  return (
    <div className={styles.modal}>
      <TitleBar {...titleBar} className={styles.title_bar} />
      <SpinnerModal {...spinnerModalProps} />
    </div>
  )
}
