import * as React from 'react'
import { connect } from 'react-redux'
import { Dispatch } from 'redux'

import * as wellSelectionSelectors from '../top-selectors/well-contents'
import { IngredientsList as IngredientsListComponent } from '../components/IngredientsList'
import { removeWellsContents } from '../labware-ingred/actions'
import { SelectedContainerId } from '../labware-ingred/reducers'
import { selectors as labwareIngredSelectors } from '../labware-ingred/selectors'
import { BaseState } from '../types'

type Props = React.ComponentProps<typeof IngredientsListComponent>
type SP = Omit<Props, 'removeWellsContents'> & {
  _labwareId: string | null | undefined
}

function mapStateToProps(state: BaseState): SP {
  const selectedLabwareId: SelectedContainerId = labwareIngredSelectors.getSelectedLabwareId(
    state
  ) as SelectedContainerId
  const labwareWellContents =
    (selectedLabwareId &&
      labwareIngredSelectors.getLiquidsByLabwareId(state)[selectedLabwareId]) ||
    {}
  return {
    liquidGroupsById: labwareIngredSelectors.getLiquidGroupsById(state),
    labwareWellContents,
    selectedIngredientGroupId: wellSelectionSelectors.getSelectedWellsCommonIngredId(
      state
    ),
    selected: false,
    _labwareId: selectedLabwareId,
  }
}

function mergeProps(
  stateProps: SP,
  dispatchProps: {
    dispatch: Dispatch<any>
  }
): Props {
  const { dispatch } = dispatchProps
  const { _labwareId, ...passThruProps } = stateProps
  return {
    ...passThruProps,
    removeWellsContents: args => {
      if (_labwareId) {
        dispatch(removeWellsContents({ ...args, labwareId: _labwareId }))
      }
    },
  }
}

export const IngredientsList = connect(
  mapStateToProps,
  // @ts-expect-error(sa, 2021-6-21): TODO: refactor to use hooks api
  null,
  mergeProps
)(IngredientsListComponent)
