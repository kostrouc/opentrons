import * as React from 'react'
import { connect } from 'react-redux'

import { selectors as stepFormSelectors } from '../../../../step-forms'
import { BaseState } from '../../../../types'
import { getDisabledPathMap } from './getDisabledPathMap'
import { Path } from './Path'

type Props = React.ComponentProps<typeof Path>
interface SP {
  disabledPathMap: Props['disabledPathMap']
}
type OP = Omit<Props, keyof SP>

function mapSTP(state: BaseState, ownProps: OP): SP {
  const {
    aspirate_airGap_checkbox,
    aspirate_airGap_volume,
    aspirate_wells,
    changeTip,
    dispense_wells,
    pipette,
    volume,
  } = ownProps
  const pipetteEntities = stepFormSelectors.getPipetteEntities(state)
  const disabledPathMap = getDisabledPathMap(
    {
      aspirate_airGap_checkbox,
      aspirate_airGap_volume,
      aspirate_wells,
      changeTip,
      dispense_wells,
      pipette,
      volume,
    },
    pipetteEntities
  )
  return {
    disabledPathMap,
  }
}

export const PathField = connect(mapSTP, () => ({}))(Path)
