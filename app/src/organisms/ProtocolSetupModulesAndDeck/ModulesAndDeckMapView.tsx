import React from 'react'

import { BaseDeck, Flex } from '@opentrons/components'
import {
  FLEX_ROBOT_TYPE,
  getSimplestDeckConfigForProtocol,
} from '@opentrons/shared-data'

import { ModuleInfo } from '../Devices/ModuleInfo'
import { getStandardDeckViewLayerBlockList } from '../Devices/ProtocolRun/utils/getStandardDeckViewLayerBlockList'

import type { CompletedProtocolAnalysis } from '@opentrons/shared-data'
import type { AttachedProtocolModuleMatch } from './utils'

interface ModulesAndDeckMapViewProps {
  attachedProtocolModuleMatches: AttachedProtocolModuleMatch[]
  runId: string
  protocolAnalysis: CompletedProtocolAnalysis | null
}

export function ModulesAndDeckMapView({
  attachedProtocolModuleMatches,
  runId,
  protocolAnalysis,
}: ModulesAndDeckMapViewProps): JSX.Element | null {
  if (protocolAnalysis == null) return null

  const deckConfig = getSimplestDeckConfigForProtocol(protocolAnalysis)

  const modulesOnDeck = attachedProtocolModuleMatches.map(module => ({
    moduleModel: module.moduleDef.model,
    moduleLocation: { slotName: module.slotName },
    moduleChildren: (
      <ModuleInfo
        moduleModel={module.moduleDef.model}
        isAttached={module.attachedModuleMatch != null}
        physicalPort={module.attachedModuleMatch?.usbPort ?? null}
        runId={runId}
      />
    ),
  }))

  return (
    <Flex height="27.75rem">
      <BaseDeck
        deckConfig={deckConfig}
        deckLayerBlocklist={getStandardDeckViewLayerBlockList(FLEX_ROBOT_TYPE)}
        robotType={FLEX_ROBOT_TYPE}
        labwareOnDeck={[]}
        modulesOnDeck={modulesOnDeck}
      />
    </Flex>
  )
}
