import * as React from 'react'
import { useSelector, useDispatch } from 'react-redux'

import { selectors as stepFormSelectors } from '../../step-forms'
import { PRESAVED_STEP_ID } from '../../steplist/types'
import {
  getHoveredTerminalItemId,
  getSelectedTerminalItemId,
  actions as stepsActions,
} from '../../ui/steps'
import { StepItem } from './StepItem'

export const PresavedStepItem = (): JSX.Element | null => {
  const presavedStepForm = useSelector(stepFormSelectors.getPresavedStepForm)
  const stepNumber = useSelector(stepFormSelectors.getOrderedStepIds).length + 1
  const hovered = useSelector(getHoveredTerminalItemId) === PRESAVED_STEP_ID
  const selected = useSelector(getSelectedTerminalItemId) === PRESAVED_STEP_ID

  // Actions
  const dispatch = useDispatch()
  const toggleStepCollapsed = (): void => {
    dispatch(stepsActions.toggleStepCollapsed(PRESAVED_STEP_ID))
  }
  const highlightStep = (): void => {
    dispatch(stepsActions.hoverOnTerminalItem(PRESAVED_STEP_ID))
  }
  const unhighlightStep = (): void => {
    dispatch(stepsActions.hoverOnTerminalItem(null))
  }

  if (presavedStepForm === null) {
    return null
  }

  const stepItemProps = {
    rawForm: null,
    stepNumber,
    stepType: presavedStepForm.stepType,

    selected,
    hovered,

    toggleStepCollapsed,
    highlightStep,
    unhighlightStep,
  }
  return <StepItem {...stepItemProps} />
}
