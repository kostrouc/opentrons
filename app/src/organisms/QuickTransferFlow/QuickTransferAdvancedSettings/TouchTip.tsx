import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { createPortal } from 'react-dom'
import {
  Flex,
  SPACING,
  DIRECTION_COLUMN,
  POSITION_FIXED,
  COLORS,
  ALIGN_CENTER,
  LargeButton,
} from '@opentrons/components'
import { getTopPortalEl } from '../../../App/portal'
import { ChildNavigation } from '../../ChildNavigation'
import { InputField } from '../../../atoms/InputField'
import { ACTIONS } from '../constants'

import type {
  QuickTransferSummaryState,
  QuickTransferSummaryAction,
  FlowRateKind,
} from '../types'
import { i18n } from '../../../i18n'
import { NumericalKeyboard } from '../../../atoms/SoftwareKeyboard'

interface TouchTipProps {
  onBack: () => void
  state: QuickTransferSummaryState
  dispatch: React.Dispatch<QuickTransferSummaryAction>
  kind: FlowRateKind
}

export function TouchTip(props: TouchTipProps): JSX.Element {
  const { kind, onBack, state, dispatch } = props
  const { t } = useTranslation('quick_transfer')
  const keyboardRef = React.useRef(null)

  const [touchTipIsEnabled, setTouchTipIsEnabled] = React.useState<boolean>(
    kind === 'aspirate'
      ? state.touchTipAspirate != null
      : state.touchTipDispense != null
  )
  const [currentStep, setCurrentStep] = React.useState<number>(1)
  const [position, setPosition] = React.useState<number | null>(
    kind === 'aspirate'
      ? state.touchTipAspirate ?? null
      : state.touchTipDispense ?? null
  )

  const touchTipAction =
    kind === 'aspirate'
      ? ACTIONS.SET_TOUCH_TIP_ASPIRATE
      : ACTIONS.SET_TOUCH_TIP_DISPENSE

  const enableTouchTipDisplayItems = [
    {
      option: true,
      description: t('option_enabled'),
      onClick: () => {
        setTouchTipIsEnabled(true)
      },
    },
    {
      option: false,
      description: t('option_disabled'),
      onClick: () => {
        setTouchTipIsEnabled(false)
      },
    },
  ]

  const handleClickBackOrExit = (): void => {
    currentStep > 1 ? setCurrentStep(currentStep - 1) : onBack()
  }

  const handleClickSaveOrContinue = (): void => {
    if (currentStep === 1) {
      if (!touchTipIsEnabled) {
        dispatch({ type: touchTipAction, position: undefined })
        onBack()
      } else {
        setCurrentStep(2)
      }
    } else if (currentStep === 2) {
      dispatch({ type: touchTipAction, position: position ?? undefined })
      onBack()
    }
  }

  const setSaveOrContinueButtonText =
    touchTipIsEnabled && currentStep < 2
      ? t('shared:continue')
      : t('shared:save')

  let wellHeight = 1
  if (kind === 'aspirate') {
    wellHeight = Math.max(
      ...state.sourceWells.map(well =>
        state.source !== null ? state.source.wells[well].depth : 0
      )
    )
  } else if (kind === 'dispense') {
    const destLabwareDefinition =
      state.destination === 'source' ? state.source : state.destination
    wellHeight = Math.max(
      ...state.destinationWells.map(well =>
        destLabwareDefinition !== null
          ? destLabwareDefinition.wells[well].depth
          : 0
      )
    )
  }

  // the allowed range for touch tip is half the height of the well to 1x the height
  const positionRange = { min: Math.round(wellHeight / 2), max: wellHeight }
  const positionError =
    position !== null &&
    (position < positionRange.min || position > positionRange.max)
      ? t(`value_out_of_range`, {
          min: positionRange.min,
          max: Math.floor(positionRange.max),
        })
      : null

  let buttonIsDisabled = false
  if (currentStep === 2) {
    buttonIsDisabled = position == null || positionError != null
  }

  return createPortal(
    <Flex position={POSITION_FIXED} backgroundColor={COLORS.white} width="100%">
      <ChildNavigation
        header={
          kind === 'aspirate'
            ? t('touch_tip_before_aspirating')
            : t('touch_tip_before_dispensing')
        }
        buttonText={i18n.format(setSaveOrContinueButtonText, 'capitalize')}
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
          {enableTouchTipDisplayItems.map(displayItem => (
            <LargeButton
              key={displayItem.description}
              buttonType={
                touchTipIsEnabled === displayItem.option
                  ? 'primary'
                  : 'secondary'
              }
              onClick={displayItem.onClick}
              buttonText={displayItem.description}
            />
          ))}
        </Flex>
      ) : null}
      {currentStep === 2 ? (
        <Flex
          alignSelf={ALIGN_CENTER}
          gridGap={SPACING.spacing48}
          paddingX={SPACING.spacing40}
          padding={`${SPACING.spacing16} ${SPACING.spacing40} ${SPACING.spacing40}`}
          marginTop="7.75rem" // using margin rather than justify due to content moving with error message
          alignItems={ALIGN_CENTER}
          height="22rem"
        >
          <Flex
            width="30.5rem"
            height="100%"
            gridGap={SPACING.spacing24}
            flexDirection={DIRECTION_COLUMN}
            marginTop={SPACING.spacing68}
          >
            <InputField
              type="number"
              value={position}
              title={t('touch_tip_position_mm')}
              error={positionError}
              readOnly
            />
          </Flex>
          <Flex
            paddingX={SPACING.spacing24}
            height="21.25rem"
            marginTop="7.75rem"
            borderRadius="0"
          >
            <NumericalKeyboard
              keyboardRef={keyboardRef}
              onChange={e => {
                setPosition(Number(e))
              }}
            />
          </Flex>
        </Flex>
      ) : null}
    </Flex>,
    getTopPortalEl()
  )
}
