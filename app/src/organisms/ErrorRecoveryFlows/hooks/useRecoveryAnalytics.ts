import { RUN_STATUS_FAILED, RUN_STATUS_SUCCEEDED } from '@opentrons/api-client'

import {
  ANALYTICS_RECOVERY_ACTION_RESULT,
  ANALYTICS_RECOVERY_ACTION_SELECTED,
  ANALYTICS_RECOVERY_ERROR_EVENT,
  ANALYTICS_RECOVERY_INITIAL_ACTION,
  ANALYTICS_RECOVERY_RUN_RESULT,
  ANALYTICS_RECOVERY_VIEW_ERROR_DETAILS,
  useTrackEvent,
} from '../../../redux/analytics'

import type { RunStatus } from '@opentrons/api-client'
import type { FailedCommand, RecoveryRoute, RouteStep } from '../types'

type InitialActionType = 'cancel-run' | 'launch-recovery'
type CommandResult = 'succeeded' | 'failed'

export interface UseRecoveryAnalyticsResult {
  /* Report the error which occurs error recovery is currently handling. */
  reportErrorEvent: (failedCommand: FailedCommand | null) => void
  /* Report which action the user selected on the recovery splash screen. */
  reportInitialActionEvent: (initialAction: InitialActionType) => void
  /* Report which recovery option the user selected. */
  reportActionSelectedEvent: (selectedRecoveryOption: RecoveryRoute) => void
  /* Report when the user views the error details and where they currently are in Error Recovery. */
  reportViewErrorDetailsEvent: (route: RecoveryRoute, step: RouteStep) => void
  /* Report the ultimate result of a selected recovery action, ie, does it result in the run resuming or does the action fail? */
  reportActionSelectedResult: (
    selectedRecoveryOption: RecoveryRoute | null,
    result: CommandResult
  ) => void
  /* Report whether the run succeeds or fails if the run entered error recovery at least once. */
  reportRecoveredRunResult: (
    runStatus: RunStatus | null,
    enteredER: boolean
  ) => void
}

export function useRecoveryAnalytics(): UseRecoveryAnalyticsResult {
  const doTrackEvent = useTrackEvent()

  const reportErrorEvent = (failedCommand: FailedCommand | null): void => {
    if (failedCommand != null) {
      doTrackEvent({
        name: ANALYTICS_RECOVERY_ERROR_EVENT,
        properties: {
          errorEvent: failedCommand.commandType,
          errorString: failedCommand.error?.detail,
        },
      })
    }
  }

  const reportInitialActionEvent = (initialAction: InitialActionType): void => {
    doTrackEvent({
      name: ANALYTICS_RECOVERY_INITIAL_ACTION,
      properties: {
        initialAction,
      },
    })
  }

  const reportActionSelectedEvent = (
    selectedRecoveryOption: RecoveryRoute
  ): void => {
    doTrackEvent({
      name: ANALYTICS_RECOVERY_ACTION_SELECTED,
      properties: {
        selectedUserAction: selectedRecoveryOption,
      },
    })
  }

  const reportViewErrorDetailsEvent = (
    route: RecoveryRoute,
    step: RouteStep
  ): void => {
    doTrackEvent({
      name: ANALYTICS_RECOVERY_VIEW_ERROR_DETAILS,
      properties: {
        route,
        step,
      },
    })
  }

  const reportActionSelectedResult = (
    selectedRecoveryOption: RecoveryRoute | null,
    result: CommandResult
  ): void => {
    if (selectedRecoveryOption != null) {
      doTrackEvent({
        name: ANALYTICS_RECOVERY_ACTION_RESULT,
        properties: {
          selectedUserAction: selectedRecoveryOption,
          result,
        },
      })
    }
  }

  const reportRecoveredRunResult = (
    runStatus: RunStatus | null,
    enteredER: boolean
  ): void => {
    if (runStatus === RUN_STATUS_SUCCEEDED || runStatus === RUN_STATUS_FAILED) {
      if (enteredER) {
        doTrackEvent({
          name: ANALYTICS_RECOVERY_RUN_RESULT,
          properties: {
            result: runStatus,
          },
        })
      }
    }
  }

  return {
    reportActionSelectedEvent,
    reportActionSelectedResult,
    reportErrorEvent,
    reportInitialActionEvent,
    reportViewErrorDetailsEvent,
    reportRecoveredRunResult,
  }
}
