import {
  RUN_STATUS_AWAITING_RECOVERY,
  RUN_STATUS_AWAITING_RECOVERY_BLOCKED_BY_OPEN_DOOR,
  RUN_STATUS_AWAITING_RECOVERY_PAUSED,
} from '@opentrons/api-client'
import { useCommandQuery } from '@opentrons/react-api-client'

import { useNotifyAllCommandsQuery } from '../../../resources/runs'

import type { RunStatus } from '@opentrons/api-client'
import type { FailedCommand } from '../types'

const ALL_COMMANDS_POLL_MS = 5000

// Return the `currentlyRecoveringFrom` command returned by the server, if any.
// Otherwise, returns null.
export function useCurrentlyRecoveringFrom(
  runId: string,
  runStatus: RunStatus | null
): FailedCommand | null {
  // There can only be a currentlyRecoveringFrom command when the run is in recovery mode.
  // In case we're falling back to polling, only enable queries when that is the case.
  const isRunInRecoveryMode = ([
    RUN_STATUS_AWAITING_RECOVERY,
    RUN_STATUS_AWAITING_RECOVERY_BLOCKED_BY_OPEN_DOOR,
    RUN_STATUS_AWAITING_RECOVERY_PAUSED,
  ] as Array<RunStatus | null>).includes(runStatus)

  const { data: allCommandsQueryData } = useNotifyAllCommandsQuery(
    runId,
    { cursor: null, pageLength: 0 }, // pageLength 0 because we only care about the links.
    {
      enabled: isRunInRecoveryMode,
      refetchInterval: ALL_COMMANDS_POLL_MS,
    }
  )
  const currentlyRecoveringFromLink =
    allCommandsQueryData?.links.currentlyRecoveringFrom

  // TODO(mm, 2024-05-21): When the server supports fetching the
  // currentlyRecoveringFrom command in one step, do that instead of this chained query.
  const { data: commandQueryData } = useCommandQuery(
    currentlyRecoveringFromLink?.meta.runId ?? null,
    currentlyRecoveringFromLink?.meta.commandId ?? null,
    {
      enabled: currentlyRecoveringFromLink != null && isRunInRecoveryMode,
    }
  )

  return isRunInRecoveryMode ? commandQueryData?.data ?? null : null
}
