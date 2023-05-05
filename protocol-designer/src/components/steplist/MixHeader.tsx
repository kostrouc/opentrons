import * as React from 'react'
import { Tooltip, useHoverTooltip, TOOLTIP_FIXED } from '@opentrons/components'
import cx from 'classnames'

import { PDListItem } from '../lists'
import { LabwareTooltipContents } from './LabwareTooltipContents'
import styles from './StepItem.css'

interface Props {
  volume?: string | null
  times?: string | null
  labwareNickname?: string | null
}

export function MixHeader(props: Props): JSX.Element {
  const { volume, times, labwareNickname } = props
  const [targetProps, tooltipProps] = useHoverTooltip({
    placement: 'bottom-start',
    strategy: TOOLTIP_FIXED,
  })
  return (
    <>
      <Tooltip {...tooltipProps}>
        <LabwareTooltipContents {...{ labwareNickname }} />
      </Tooltip>

      <PDListItem className={styles.step_subitem}>
        <span
          {...targetProps}
          className={cx(styles.emphasized_cell, styles.labware_display_name)}
        >
          {labwareNickname}
        </span>

        <span>{volume} uL</span>
        <span>{times}x</span>
      </PDListItem>
    </>
  )
}
