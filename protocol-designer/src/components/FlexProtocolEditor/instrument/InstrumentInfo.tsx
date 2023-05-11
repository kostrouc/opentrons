import * as React from 'react'
import cx from 'classnames'

import { InfoItem } from './InfoItem'
import { InstrumentDiagram } from './InstrumentDiagram'
import styles from './instrument.css'

import type { InstrumentDiagramProps } from './InstrumentDiagram'
import { Mount } from '@opentrons/components/src/robot-types'
import { Card } from '@opentrons/components'

export interface InstrumentInfoProps {
  /** 'left' or 'right' */
  mount: Mount
  /** if true, show labels 'LEFT PIPETTE' / 'RIGHT PIPETTE' */
  showMountLabel?: boolean | null
  /** human-readable description, eg 'p300 Single-channel' */
  description: string
  /** paired tiprack model */
  tiprackModel?: string
  /** if disabled, pipette & its info are grayed out */
  isDisabled: boolean
  /** specs of mounted pipette */
  pipetteSpecs?: InstrumentDiagramProps['pipetteSpecs'] | null
  /** classes to apply */
  className?: string
  /** classes to apply to the info group child */
  infoClassName?: string
  /** children to display under the info */
  children?: React.ReactNode
}

export function InstrumentInfo(props: InstrumentInfoProps): JSX.Element {
  const className = cx(
    styles.pipette,
    styles[props.mount],
    { [styles.disabled]: props.isDisabled },
    props.className
  )
  return (
    <div style={{ marginBottom: 10 }}>
      <Card>
        <div className={className}>
          <InstrumentDiagram
            pipetteSpecs={props.pipetteSpecs}
            className={styles.pipette_icon}
            mount={props.mount}
          />

          <div className={cx(styles.pipette_info, props.infoClassName)}>
            <InfoItem
              title={
                props.showMountLabel ? `${props.mount} pipette` : `pipette`
              }
              value={props.description}
            />
            {props.tiprackModel && (
              <InfoItem title={'tip rack'} value={props.tiprackModel} />
            )}
            {props.children}
          </div>
        </div>
      </Card>
    </div>
  )
}
