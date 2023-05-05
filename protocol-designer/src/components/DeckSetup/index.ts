import { connect } from 'react-redux'

import * as labwareIngredActions from '../../labware-ingred/actions'
import { selectors as labwareIngredSelectors } from '../../labware-ingred/selectors'
import {
  selectors as stepFormSelectors,
  InitialDeckSetup,
} from '../../step-forms'
import { TerminalItemId } from '../../steplist'
import { BaseState, ThunkDispatch } from '../../types'
import { getSelectedTerminalItemId } from '../../ui/steps'
import { DeckSetup as DeckSetupComponent, DeckSetupProps } from './DeckSetup'

type Props = DeckSetupProps
interface SP {
  selectedTerminalItemId?: TerminalItemId | null
  drilledDown: boolean
  initialDeckSetup: InitialDeckSetup
}
interface DP {
  drillUpFromLabware: () => unknown
}

const mapStateToProps = (state: BaseState): SP => ({
  selectedTerminalItemId: getSelectedTerminalItemId(state),
  drilledDown: labwareIngredSelectors.getDrillDownLabwareId(state) != null,
  initialDeckSetup: stepFormSelectors.getInitialDeckSetup(state),
})

const mapDispatchToProps = (dispatch: ThunkDispatch<any>): DP => ({
  drillUpFromLabware: () => dispatch(labwareIngredActions.drillUpFromLabware()),
})

const mergeProps = (stateProps: SP, dispatchProps: DP): Props => ({
  selectedTerminalItemId: stateProps.selectedTerminalItemId,
  drilledDown: stateProps.drilledDown,
  initialDeckSetup: stateProps.initialDeckSetup,
  handleClickOutside: () => {
    if (stateProps.drilledDown) dispatchProps.drillUpFromLabware()
  },
})

export const DeckSetup = connect(
  mapStateToProps,
  mapDispatchToProps,
  mergeProps
)(DeckSetupComponent)
