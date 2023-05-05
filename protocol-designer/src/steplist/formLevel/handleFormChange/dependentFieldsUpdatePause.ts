/* eslint-disable import/no-default-export */
import pick from 'lodash/pick'

import { FormData, StepFieldName } from '../../../form-types'
import { FormPatch } from '../../actions/types'
import { getDefaultsForStepType } from '../getDefaultsForStepType'
import { chainPatchUpdaters, fieldHasChanged } from './utils'

// TODO: Ian 2019-02-21 import this from a more central place - see #2926
const getDefaultFields = (...fields: StepFieldName[]): FormPatch =>
  pick(getDefaultsForStepType('pause'), fields)

const updatePatchOnPauseTemperatureChange = (
  patch: FormPatch,
  rawForm: FormData
): FormPatch => {
  if (fieldHasChanged(rawForm, patch, 'pauseAction')) {
    return {
      ...patch,
      ...getDefaultFields(
        'pauseTemperature',
        'pauseHour',
        'pauseMinute',
        'pauseSecond'
      ),
    }
  }

  return patch
}

export function dependentFieldsUpdatePause(
  originalPatch: FormPatch,
  rawForm: FormData // raw = NOT hydrated
): FormPatch {
  // sequentially modify parts of the patch until it's fully updated
  return chainPatchUpdaters(originalPatch, [
    chainPatch => updatePatchOnPauseTemperatureChange(chainPatch, rawForm),
  ])
}
