import * as React from 'react'
import { DIRECTION_COLUMN, Flex, SPACING } from '@opentrons/components'
import { useInstrumentsQuery } from '@opentrons/react-api-client'

import { onDeviceDisplayRoutes } from '../../App/OnDeviceDisplayApp'
import { GripperWizardFlows } from '../../organisms/GripperWizardFlows'
import { AttachedInstrumentMountItem } from '../../organisms/InstrumentMountItem'
import { Navigation } from '../../organisms/OnDeviceDisplay/Navigation'
import { PipetteWizardFlows } from '../../organisms/PipetteWizardFlows'

export const InstrumentsDashboard = (): JSX.Element => {
  const { data: attachedInstruments } = useInstrumentsQuery()
  const [wizardProps, setWizardProps] = React.useState<
    | React.ComponentProps<typeof GripperWizardFlows>
    | React.ComponentProps<typeof PipetteWizardFlows>
    | null
  >(null)

  return (
    <Flex paddingX={SPACING.spacingXXL} flexDirection={DIRECTION_COLUMN}>
      <Navigation routes={onDeviceDisplayRoutes} />
      <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacing3}>
        <AttachedInstrumentMountItem
          mount="left"
          attachedInstrument={
            (attachedInstruments?.data ?? []).find(i => i.mount === 'left') ??
            null
          }
          setWizardProps={setWizardProps}
        />
        <AttachedInstrumentMountItem
          mount="right"
          attachedInstrument={
            (attachedInstruments?.data ?? []).find(i => i.mount === 'right') ??
            null
          }
          setWizardProps={setWizardProps}
        />
        <AttachedInstrumentMountItem
          mount="extension"
          attachedInstrument={
            (attachedInstruments?.data ?? []).find(
              i => i.mount === 'extension'
            ) ?? null
          }
          setWizardProps={setWizardProps}
        />
      </Flex>
      {wizardProps != null && 'mount' in wizardProps ? (
        <PipetteWizardFlows {...wizardProps} />
      ) : null}
      {wizardProps != null && !('mount' in wizardProps) ? (
        <GripperWizardFlows {...wizardProps} />
      ) : null}
    </Flex>
  )
}
