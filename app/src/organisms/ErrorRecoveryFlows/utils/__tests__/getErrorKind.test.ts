import { describe, expect, it } from 'vitest'

import { ERROR_KINDS, DEFINED_ERROR_TYPES } from '../../constants'
import { getErrorKind } from '../getErrorKind'

import type { RunCommandError, RunTimeCommand } from '@opentrons/shared-data'

describe('getErrorKind', () => {
  it(`returns ${ERROR_KINDS.NO_LIQUID_DETECTED} for ${DEFINED_ERROR_TYPES.LIQUID_NOT_FOUND} errorType`, () => {
    const result = getErrorKind({
      commandType: 'liquidProbe',
      error: {
        isDefined: true,
        errorType: DEFINED_ERROR_TYPES.LIQUID_NOT_FOUND,
      } as RunCommandError,
    } as RunTimeCommand)
    expect(result).toEqual(ERROR_KINDS.NO_LIQUID_DETECTED)
  })

  it(`returns ${ERROR_KINDS.OVERPRESSURE_WHILE_ASPIRATING} for ${DEFINED_ERROR_TYPES.OVERPRESSURE} errorType`, () => {
    const result = getErrorKind({
      commandType: 'aspirate',
      error: {
        isDefined: true,
        errorType: DEFINED_ERROR_TYPES.OVERPRESSURE,
      } as RunCommandError,
    } as RunTimeCommand)
    expect(result).toEqual(ERROR_KINDS.OVERPRESSURE_WHILE_ASPIRATING)
  })

  it(`returns ${ERROR_KINDS.OVERPRESSURE_WHILE_DISPENSING} for ${DEFINED_ERROR_TYPES.OVERPRESSURE} errorType`, () => {
    const result = getErrorKind({
      commandType: 'dispense',
      error: {
        isDefined: true,
        errorType: DEFINED_ERROR_TYPES.OVERPRESSURE,
      } as RunCommandError,
    } as RunTimeCommand)
    expect(result).toEqual(ERROR_KINDS.OVERPRESSURE_WHILE_DISPENSING)
  })

  it(`returns ${ERROR_KINDS.GENERAL_ERROR} for undefined errors`, () => {
    const result = getErrorKind({
      commandType: 'aspirate',
      error: {
        isDefined: false,
        // It should treat this error as undefined because isDefined===false,
        // even though the errorType happens to match a defined error.
        errorType: DEFINED_ERROR_TYPES.OVERPRESSURE,
      } as RunCommandError,
    } as RunTimeCommand)
    expect(result).toEqual(ERROR_KINDS.GENERAL_ERROR)
  })

  it(`returns ${ERROR_KINDS.GENERAL_ERROR} for defined errors not handled explicitly`, () => {
    const result = getErrorKind({
      commandType: 'aspirate',
      error: ({
        isDefined: true,
        errorType: 'someHithertoUnknownDefinedErrorType',
      } as unknown) as RunCommandError,
    } as RunTimeCommand)
    expect(result).toEqual(ERROR_KINDS.GENERAL_ERROR)
  })
})
