import { ERROR_KINDS, DEFINED_ERROR_TYPES } from '../constants'

import type { RunTimeCommand } from '@opentrons/shared-data'
import type { ErrorKind } from '../types'

/**
 * Given server-side information about a failed command,
 * decide which UI flow to present to recover from it.
 */
export function getErrorKind(failedCommand: RunTimeCommand | null): ErrorKind {
  const commandType = failedCommand?.commandType
  const errorIsDefined = failedCommand?.error?.isDefined ?? false
  const errorType = failedCommand?.error?.errorType

  if (errorIsDefined) {
    if (
      commandType === 'aspirate' &&
      errorType === DEFINED_ERROR_TYPES.OVERPRESSURE
    )
      return ERROR_KINDS.OVERPRESSURE_WHILE_ASPIRATING
    else if (
      commandType === 'dispense' &&
      errorType === DEFINED_ERROR_TYPES.OVERPRESSURE
    )
      return ERROR_KINDS.OVERPRESSURE_WHILE_DISPENSING
    else if (
      commandType === 'liquidProbe' &&
      errorType === DEFINED_ERROR_TYPES.LIQUID_NOT_FOUND
    )
      return ERROR_KINDS.NO_LIQUID_DETECTED
    // todo(mm, 2024-07-02): Also handle aspirateInPlace and dispenseInPlace.
    // https://opentrons.atlassian.net/browse/EXEC-593
  }

  return ERROR_KINDS.GENERAL_ERROR
}
