import type { ModuleOnlyParams } from '@opentrons/shared-data/protocol/types/schemaV6/command/module'

import type { CommandCreator } from '../../types'
import { uuid } from '../../utils'

export const heaterShakerStopShake: CommandCreator<ModuleOnlyParams> = (
  args,
  invariantContext,
  prevRobotState
) => {
  return {
    commands: [
      {
        commandType: 'heaterShaker/deactivateShaker',
        key: uuid(),
        params: {
          moduleId: args.moduleId,
        },
      },
    ],
  }
}
