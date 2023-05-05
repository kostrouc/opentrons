import type { ModuleOnlyParams } from '@opentrons/shared-data/protocol/types/schemaV4'

import type { CommandCreator } from '../../types'
import { uuid } from '../../utils'

export const thermocyclerOpenLid: CommandCreator<ModuleOnlyParams> = (
  args,
  invariantContext,
  prevRobotState
) => {
  return {
    commands: [
      {
        commandType: 'thermocycler/openLid',
        key: uuid(),
        params: {
          moduleId: args.module,
        },
      },
    ],
  }
}
