import * as React from 'react'
import { useTranslation } from 'react-i18next'
import {
  Flex,
  DIRECTION_ROW,
  JUSTIFY_SPACE_BETWEEN,
  Chip,
} from '@opentrons/components'

import type { LabwareOffset } from '@opentrons/api-client'
import { useToaster } from '../../organisms/ToasterOven'
import { ODDBackButton } from '../../molecules/ODDBackButton'
import { FloatingActionButton, SmallButton } from '../../atoms/buttons'
import type { SetupScreens } from '../../pages/ProtocolSetup'
import { useMostRecentCompletedAnalysis } from '../LabwarePositionCheck/useMostRecentCompletedAnalysis'
import { TerseOffsetTable } from '../../organisms/LabwarePositionCheck/ResultsSummary'
import { getLabwareDefinitionsFromCommands } from '../../molecules/Command/utils/getLabwareDefinitionsFromCommands'
import { useNotifyRunQuery } from '../../resources/runs'
import { getLatestCurrentOffsets } from '../../organisms/Devices/ProtocolRun/SetupLabwarePositionCheck/utils'

export interface ProtocolSetupOffsetsProps {
  runId: string
  setSetupScreen: React.Dispatch<React.SetStateAction<SetupScreens>>
  lpcDisabledReason: string | null
  launchLPC: () => void
  LPCWizard: JSX.Element | null
  isConfirmed: boolean
  setIsConfirmed: (confirmed: boolean) => void
}

export function ProtocolSetupOffsets({
  runId,
  setSetupScreen,
  isConfirmed,
  setIsConfirmed,
  launchLPC,
  lpcDisabledReason,
  LPCWizard,
}: ProtocolSetupOffsetsProps): JSX.Element {
  const { t } = useTranslation('protocol_setup')
  const { makeSnackbar } = useToaster()
  const mostRecentAnalysis = useMostRecentCompletedAnalysis(runId)
  const makeDisabledReasonSnackbar = (): void => {
    if (lpcDisabledReason != null) {
      makeSnackbar(lpcDisabledReason)
    }
  }

  const labwareDefinitions = getLabwareDefinitionsFromCommands(
    mostRecentAnalysis?.commands ?? []
  )
  const { data: runRecord } = useNotifyRunQuery(runId, { staleTime: Infinity })
  const currentOffsets = runRecord?.data?.labwareOffsets ?? []
  const sortedOffsets: LabwareOffset[] =
    currentOffsets.length > 0
      ? currentOffsets
          .map(offset => ({
            ...offset,
            //  convert into date to sort
            createdAt: new Date(offset.createdAt),
          }))
          .sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime())
          .map(offset => ({
            ...offset,
            //   convert back into string
            createdAt: offset.createdAt.toISOString(),
          }))
      : []
  const nonIdentityOffsets = getLatestCurrentOffsets(sortedOffsets)
  return (
    <>
      {LPCWizard}
      {LPCWizard == null && (
        <>
          <Flex
            flexDirection={DIRECTION_ROW}
            justifyContent={JUSTIFY_SPACE_BETWEEN}
          >
            <ODDBackButton
              label={t('labware_position_check')}
              onClick={() => {
                setSetupScreen('prepare to run')
              }}
            />
            {isConfirmed ? (
              <Chip
                background
                iconName="ot-check"
                text={t('placements_ready')}
                type="success"
                chipSize="small"
              />
            ) : (
              <SmallButton
                buttonText={t('confirm_placements')}
                onClick={() => {
                  setIsConfirmed(true)
                  setSetupScreen('prepare to run')
                }}
              />
            )}
          </Flex>
          <TerseOffsetTable
            offsets={nonIdentityOffsets}
            labwareDefinitions={labwareDefinitions}
          />
          <FloatingActionButton
            buttonText={t('update_offsets')}
            iconName="reticle"
            onClick={() => {
              if (lpcDisabledReason != null) {
                makeDisabledReasonSnackbar()
              } else {
                launchLPC()
              }
            }}
          />
        </>
      )}
    </>
  )
}
