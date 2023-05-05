import { useCalibrationStatusQuery } from '@opentrons/react-api-client'

import type { DeckCalibrationStatus } from '../../../redux/calibration/types'
import { useRobot } from './useRobot'

export function useDeckCalibrationStatus(
  robotName: string | null = null
): DeckCalibrationStatus | null {
  const robot = useRobot(robotName)
  return (
    useCalibrationStatusQuery(
      {},
      robot?.ip != null ? { hostname: robot.ip } : null
    )?.data?.deckCalibration?.status ?? null
  )
}
