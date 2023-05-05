import { LabwareDefinition2 } from '@opentrons/shared-data'
import { orderWells } from '@opentrons/step-generation'
import intersection from 'lodash/intersection'

import { WellOrderOption } from '../../form-types'

export function getOrderedWells(
  unorderedWells: string[],
  labwareDef: LabwareDefinition2,
  wellOrderFirst: WellOrderOption,
  wellOrderSecond: WellOrderOption
): string[] {
  const allWellsOrdered = orderWells(
    labwareDef.ordering,
    wellOrderFirst,
    wellOrderSecond
  )
  return intersection(allWellsOrdered, unorderedWells)
}
