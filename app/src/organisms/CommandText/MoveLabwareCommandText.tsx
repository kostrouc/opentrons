import { useTranslation } from 'react-i18next'
import { GRIPPER_WASTE_CHUTE_ADDRESSABLE_AREA } from '@opentrons/shared-data'
import { getLabwareName } from './utils'
import { getLabwareDisplayLocation } from './utils/getLabwareDisplayLocation'
import { getFinalLabwareLocation } from './utils/getFinalLabwareLocation'

import type {
  CompletedProtocolAnalysis,
  MoveLabwareRunTimeCommand,
  RobotType,
  ProtocolAnalysisOutput,
} from '@opentrons/shared-data'

interface MoveLabwareCommandTextProps {
  command: MoveLabwareRunTimeCommand
  analysis: CompletedProtocolAnalysis | ProtocolAnalysisOutput
  robotType: RobotType
}
export function MoveLabwareCommandText(
  props: MoveLabwareCommandTextProps
): JSX.Element {
  const { t } = useTranslation('protocol_command_text')
  const { command, analysis, robotType } = props
  const { labwareId, newLocation, strategy } = command.params

  const allPreviousCommands = analysis.commands.slice(
    0,
    analysis.commands.findIndex(c => c.id === command.id)
  )
  const oldLocation = getFinalLabwareLocation(labwareId, allPreviousCommands)
  const newDisplayLocation = getLabwareDisplayLocation(
    analysis,
    newLocation,
    t,
    robotType
  )

  const location = newDisplayLocation.includes(
    GRIPPER_WASTE_CHUTE_ADDRESSABLE_AREA
  )
    ? 'Waste Chute'
    : newDisplayLocation

  return strategy === 'usingGripper'
    ? t('move_labware_using_gripper', {
        labware: getLabwareName(analysis, labwareId),
        old_location:
          oldLocation != null
            ? getLabwareDisplayLocation(
                analysis,
                oldLocation,
                t,
                robotType
              )
            : '',
        new_location: location,
      })
    : t('move_labware_manually', {
        labware: getLabwareName(analysis, labwareId),
        old_location:
          oldLocation != null
            ? getLabwareDisplayLocation(
                analysis,
                oldLocation,
                t,
                robotType
              )
            : '',
        new_location: location,
      })
}
