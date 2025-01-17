import * as React from 'react'
import head from 'lodash/head'

import {
  useResumeRunFromRecoveryMutation,
  useStopRunMutation,
  useUpdateErrorRecoveryPolicy,
} from '@opentrons/react-api-client'

import { useChainRunCommands } from '../../../resources/runs'
import { RECOVERY_MAP } from '../constants'

import type {
  CreateCommand,
  LoadedLabware,
  MoveToCoordinatesCreateCommand,
  AspirateInPlaceRunTimeCommand,
  BlowoutInPlaceRunTimeCommand,
  DispenseInPlaceRunTimeCommand,
  DropTipInPlaceRunTimeCommand,
  PrepareToAspirateRunTimeCommand,
} from '@opentrons/shared-data'
import type {
  CommandData,
  RecoveryPolicyRulesParams,
} from '@opentrons/api-client'
import type { WellGroup } from '@opentrons/components'
import type { FailedCommand } from '../types'
import type { UseFailedLabwareUtilsResult } from './useFailedLabwareUtils'
import type { UseRouteUpdateActionsResult } from './useRouteUpdateActions'
import type { RecoveryToasts } from './useRecoveryToasts'
import type { UseRecoveryAnalyticsResult } from './useRecoveryAnalytics'
import type { CurrentRecoveryOptionUtils } from './useRecoveryRouting'

interface UseRecoveryCommandsParams {
  runId: string
  failedCommand: FailedCommand | null
  failedLabwareUtils: UseFailedLabwareUtilsResult
  routeUpdateActions: UseRouteUpdateActionsResult
  recoveryToastUtils: RecoveryToasts
  analytics: UseRecoveryAnalyticsResult
  selectedRecoveryOption: CurrentRecoveryOptionUtils['selectedRecoveryOption']
}
export interface UseRecoveryCommandsResult {
  /* A terminal recovery command that causes ER to exit as the run status becomes "running" */
  resumeRun: () => void
  /* A terminal recovery command that causes ER to exit as the run status becomes "stop-requested" */
  cancelRun: () => void
  /* A terminal recovery command, that causes ER to exit as the run status becomes "running" */
  skipFailedCommand: () => void
  /* A non-terminal recovery command. Ignore this errorKind for the rest of this run. */
  ignoreErrorKindThisRun: () => Promise<void>
  /* A non-terminal recovery command */
  retryFailedCommand: () => Promise<CommandData[]>
  /* A non-terminal recovery command */
  homePipetteZAxes: () => Promise<CommandData[]>
  /* A non-terminal recovery command */
  pickUpTips: () => Promise<CommandData[]>
}

// TODO(jh, 07-24-24): Create tighter abstractions for terminal vs. non-terminal commands.
// Returns commands with a "fixit" intent. Commands may or may not terminate Error Recovery. See each command docstring for details.
export function useRecoveryCommands({
  runId,
  failedCommand,
  failedLabwareUtils,
  routeUpdateActions,
  recoveryToastUtils,
  analytics,
  selectedRecoveryOption,
}: UseRecoveryCommandsParams): UseRecoveryCommandsResult {
  const { proceedToRouteAndStep } = routeUpdateActions
  const { chainRunCommands } = useChainRunCommands(runId, failedCommand?.id)
  const {
    mutateAsync: resumeRunFromRecovery,
  } = useResumeRunFromRecoveryMutation()
  const { stopRun } = useStopRunMutation()
  const { updateErrorRecoveryPolicy } = useUpdateErrorRecoveryPolicy(runId)
  const { makeSuccessToast } = recoveryToastUtils

  const buildRetryPrepMove = (): MoveToCoordinatesCreateCommand | null => {
    type InPlaceCommand =
      | AspirateInPlaceRunTimeCommand
      | BlowoutInPlaceRunTimeCommand
      | DispenseInPlaceRunTimeCommand
      | DropTipInPlaceRunTimeCommand
      | PrepareToAspirateRunTimeCommand
    const IN_PLACE_COMMAND_TYPES = [
      'aspirateInPlace',
      'dispenseInPlace',
      'blowOutInPlace',
      'dropTipInPlace',
      'prepareToAspirate',
    ] as const
    const isInPlace = (
      failedCommand: FailedCommand
    ): failedCommand is InPlaceCommand =>
      IN_PLACE_COMMAND_TYPES.includes(
        (failedCommand as InPlaceCommand).commandType
      )
    return failedCommand != null
      ? isInPlace(failedCommand)
        ? failedCommand.error?.isDefined &&
          failedCommand.error?.errorType === 'overpressure' &&
          // Paranoia: this value comes from the wire and may be unevenly implemented
          typeof failedCommand.error?.errorInfo?.retryLocation?.at(0) ===
            'number'
          ? {
              commandType: 'moveToCoordinates',
              intent: 'fixit',
              params: {
                pipetteId: failedCommand.params?.pipetteId,
                coordinates: {
                  x: failedCommand.error.errorInfo.retryLocation[0],
                  y: failedCommand.error.errorInfo.retryLocation[1],
                  z: failedCommand.error.errorInfo.retryLocation[2],
                },
              },
            }
          : null
        : null
      : null
  }
  const chainRunRecoveryCommands = React.useCallback(
    (
      commands: CreateCommand[],
      continuePastFailure: boolean = false
    ): Promise<CommandData[]> =>
      chainRunCommands(commands, continuePastFailure).catch(e => {
        console.warn(`Error executing "fixit" command: ${e}`)
        analytics.reportActionSelectedResult(selectedRecoveryOption, 'failed')
        // the catch never occurs if continuePastCommandFailure is "true"
        void proceedToRouteAndStep(RECOVERY_MAP.ERROR_WHILE_RECOVERING.ROUTE)
        return Promise.reject(new Error(`Could not execute command: ${e}`))
      }),
    [chainRunCommands]
  )

  const retryFailedCommand = React.useCallback((): Promise<CommandData[]> => {
    const { commandType, params } = failedCommand as FailedCommand // Null case is handled before command could be issued.
    return chainRunRecoveryCommands(
      [
        // move back to the location of the command if it is an in-place command
        buildRetryPrepMove(),
        { commandType, params }, // retry the command that failed
      ].filter(c => c != null) as CreateCommand[]
    ) // the created command is the same command that failed
  }, [chainRunRecoveryCommands, failedCommand])

  // Homes the Z-axis of all attached pipettes.
  const homePipetteZAxes = React.useCallback((): Promise<CommandData[]> => {
    return chainRunRecoveryCommands([HOME_PIPETTE_Z_AXES])
  }, [chainRunRecoveryCommands])

  // Pick up the user-selected tips
  const pickUpTips = React.useCallback((): Promise<CommandData[]> => {
    const { selectedTipLocations, failedLabware } = failedLabwareUtils

    const pickUpTipCmd = buildPickUpTips(
      selectedTipLocations,
      failedCommand,
      failedLabware
    )

    if (pickUpTipCmd == null) {
      return Promise.reject(new Error('Invalid use of pickUpTips command'))
    } else {
      return chainRunRecoveryCommands([pickUpTipCmd])
    }
  }, [chainRunRecoveryCommands, failedCommand, failedLabwareUtils])

  const resumeRun = React.useCallback((): void => {
    void resumeRunFromRecovery(runId).then(() => {
      analytics.reportActionSelectedResult(selectedRecoveryOption, 'succeeded')
      makeSuccessToast()
    })
  }, [runId, resumeRunFromRecovery, makeSuccessToast])

  const cancelRun = React.useCallback((): void => {
    analytics.reportActionSelectedResult(selectedRecoveryOption, 'succeeded')
    stopRun(runId)
  }, [runId])

  const skipFailedCommand = React.useCallback((): void => {
    void resumeRunFromRecovery(runId).then(() => {
      analytics.reportActionSelectedResult(selectedRecoveryOption, 'succeeded')
      makeSuccessToast()
    })
  }, [runId, resumeRunFromRecovery, makeSuccessToast])

  const ignoreErrorKindThisRun = React.useCallback((): Promise<void> => {
    if (failedCommand?.error != null) {
      const ignorePolicyRules = buildIgnorePolicyRules(
        failedCommand.commandType,
        failedCommand.error.errorType
      )

      updateErrorRecoveryPolicy(ignorePolicyRules)
      return Promise.resolve()
    } else {
      return Promise.reject(
        new Error('Could not execute command. No failed command.')
      )
    }
  }, [failedCommand?.error?.errorType, failedCommand?.commandType])

  return {
    resumeRun,
    cancelRun,
    retryFailedCommand,
    homePipetteZAxes,
    pickUpTips,
    skipFailedCommand,
    ignoreErrorKindThisRun,
  }
}

export const HOME_PIPETTE_Z_AXES: CreateCommand = {
  commandType: 'home',
  params: { axes: ['leftZ', 'rightZ'] },
  intent: 'fixit',
}

export const buildPickUpTips = (
  tipGroup: WellGroup | null,
  failedCommand: FailedCommand | null,
  labware: LoadedLabware | null
): CreateCommand | null => {
  if (
    failedCommand == null ||
    labware === null ||
    tipGroup == null ||
    !('pipetteId' in failedCommand.params)
  ) {
    return null
  } else {
    const wellName = head(Object.keys(tipGroup)) as string

    return {
      commandType: 'pickUpTip',
      params: {
        labwareId: labware.id,
        pipetteId: failedCommand.params.pipetteId,
        wellName,
      },
    }
  }
}

export const buildIgnorePolicyRules = (
  commandType: FailedCommand['commandType'],
  errorType: string
): RecoveryPolicyRulesParams => {
  return [
    {
      commandType,
      errorType,
      ifMatch: 'ignoreAndContinue',
    },
  ]
}
