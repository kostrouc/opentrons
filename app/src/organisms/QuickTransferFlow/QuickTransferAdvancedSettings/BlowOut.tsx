import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { createPortal } from 'react-dom'
import {
  Flex,
  SPACING,
  DIRECTION_COLUMN,
  POSITION_FIXED,
  LargeButton,
  COLORS,
} from '@opentrons/components'
import {
  WASTE_CHUTE_FIXTURES,
  FLEX_SINGLE_SLOT_BY_CUTOUT_ID,
  TRASH_BIN_ADAPTER_FIXTURE,
} from '@opentrons/shared-data'
import { getTopPortalEl } from '../../../App/portal'
import { useNotifyDeckConfigurationQuery } from '../../../resources/deck_configuration'
import { ChildNavigation } from '../../ChildNavigation'
import { ACTIONS } from '../constants'

import type { DeckConfiguration } from '@opentrons/shared-data'
import type {
  QuickTransferSummaryState,
  QuickTransferSummaryAction,
  FlowRateKind,
  BlowOutLocation,
  TransferType,
} from '../types'
import { i18n } from '../../../i18n'

interface BlowOutProps {
  onBack: () => void
  state: QuickTransferSummaryState
  dispatch: React.Dispatch<QuickTransferSummaryAction>
  kind: FlowRateKind
}

export const useBlowOutLocationOptions = (
  deckConfig: DeckConfiguration,
  transferType: TransferType
): Array<{ location: BlowOutLocation; description: string }> => {
  const { t } = useTranslation('quick_transfer')

  const trashLocations = deckConfig.filter(
    cutoutConfig =>
      WASTE_CHUTE_FIXTURES.includes(cutoutConfig.cutoutFixtureId) ||
      TRASH_BIN_ADAPTER_FIXTURE === cutoutConfig.cutoutFixtureId
  )

  // add trash bin in A3 if no trash or waste chute configured
  if (trashLocations.length === 0) {
    trashLocations.push({
      cutoutId: 'cutoutA3',
      cutoutFixtureId: TRASH_BIN_ADAPTER_FIXTURE,
    })
  }
  const blowOutLocationItems: Array<{
    location: BlowOutLocation
    description: string
  }> = []
  if (transferType !== 'distribute') {
    blowOutLocationItems.push({
      location: 'dest_well',
      description: t('blow_out_destination_well'),
    })
  }
  if (transferType !== 'consolidate') {
    blowOutLocationItems.push({
      location: 'source_well',
      description: t('blow_out_source_well'),
    })
  }
  trashLocations.forEach(location => {
    blowOutLocationItems.push({
      location,
      description:
        location.cutoutFixtureId === TRASH_BIN_ADAPTER_FIXTURE
          ? t('trashBin_location', {
              slotName: FLEX_SINGLE_SLOT_BY_CUTOUT_ID[location.cutoutId],
            })
          : t('wasteChute_location', {
              slotName: FLEX_SINGLE_SLOT_BY_CUTOUT_ID[location.cutoutId],
            }),
    })
  })
  return blowOutLocationItems
}

export function BlowOut(props: BlowOutProps): JSX.Element {
  const { onBack, state, dispatch } = props
  const { t } = useTranslation('quick_transfer')
  const deckConfig = useNotifyDeckConfigurationQuery().data ?? []

  const [isBlowOutEnabled, setisBlowOutEnabled] = React.useState<boolean>(
    state.blowOut != null
  )
  const [currentStep, setCurrentStep] = React.useState<number>(1)
  const [blowOutLocation, setBlowOutLocation] = React.useState<
    BlowOutLocation | undefined
  >(state.blowOut)

  const enableBlowOutDisplayItems = [
    {
      value: true,
      description: t('option_enabled'),
      onClick: () => {
        setisBlowOutEnabled(true)
      },
    },
    {
      value: false,
      description: t('option_disabled'),
      onClick: () => {
        setisBlowOutEnabled(false)
      },
    },
  ]

  const blowOutLocationItems = useBlowOutLocationOptions(
    deckConfig,
    state.transferType
  )

  const handleClickBackOrExit = (): void => {
    currentStep > 1 ? setCurrentStep(currentStep - 1) : onBack()
  }

  const handleClickSaveOrContinue = (): void => {
    if (currentStep === 1) {
      if (!isBlowOutEnabled) {
        dispatch({
          type: ACTIONS.SET_BLOW_OUT,
          location: undefined,
        })
        onBack()
      } else {
        setCurrentStep(currentStep + 1)
      }
    } else {
      dispatch({
        type: ACTIONS.SET_BLOW_OUT,
        location: blowOutLocation,
      })
      onBack()
    }
  }

  const saveOrContinueButtonText =
    isBlowOutEnabled && currentStep < 2
      ? t('shared:continue')
      : t('shared:save')

  let buttonIsDisabled = false
  if (currentStep === 2) {
    buttonIsDisabled = blowOutLocation == null
  }

  return createPortal(
    <Flex position={POSITION_FIXED} backgroundColor={COLORS.white} width="100%">
      <ChildNavigation
        header={t('blow_out_after_dispensing')}
        buttonText={i18n.format(saveOrContinueButtonText, 'capitalize')}
        onClickBack={handleClickBackOrExit}
        onClickButton={handleClickSaveOrContinue}
        top={SPACING.spacing8}
        buttonIsDisabled={buttonIsDisabled}
      />
      {currentStep === 1 ? (
        <Flex
          marginTop={SPACING.spacing120}
          flexDirection={DIRECTION_COLUMN}
          padding={`${SPACING.spacing16} ${SPACING.spacing60} ${SPACING.spacing40} ${SPACING.spacing60}`}
          gridGap={SPACING.spacing4}
          width="100%"
        >
          {enableBlowOutDisplayItems.map(displayItem => (
            <LargeButton
              key={displayItem.description}
              buttonType={
                displayItem.value === isBlowOutEnabled ? 'primary' : 'secondary'
              }
              onClick={() => {
                setisBlowOutEnabled(displayItem.value)
              }}
              buttonText={displayItem.description}
            />
          ))}
        </Flex>
      ) : null}
      {currentStep === 2 ? (
        <Flex
          marginTop={SPACING.spacing120}
          flexDirection={DIRECTION_COLUMN}
          padding={`${SPACING.spacing16} ${SPACING.spacing60} ${SPACING.spacing40} ${SPACING.spacing60}`}
          gridGap={SPACING.spacing4}
          width="100%"
        >
          {blowOutLocationItems.map(blowOutLocationItem => (
            <LargeButton
              key={blowOutLocationItem.description}
              buttonType={
                blowOutLocation === blowOutLocationItem.location
                  ? 'primary'
                  : 'secondary'
              }
              onClick={() => {
                setBlowOutLocation(
                  blowOutLocationItem.location as BlowOutLocation
                )
              }}
              buttonText={blowOutLocationItem.description}
            />
          ))}
        </Flex>
      ) : null}
    </Flex>,
    getTopPortalEl()
  )
}
