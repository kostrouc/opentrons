import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { createPortal } from 'react-dom'
import {
  Flex,
  SPACING,
  DIRECTION_COLUMN,
  POSITION_FIXED,
  COLORS,
  LargeButton,
  ALIGN_CENTER,
} from '@opentrons/components'
import { useNotifyDeckConfigurationQuery } from '../../../resources/deck_configuration'
import { getTopPortalEl } from '../../../App/portal'
import { ChildNavigation } from '../../ChildNavigation'
import { useBlowOutLocationOptions } from './BlowOut'
import { getVolumeRange } from '../utils'

import type {
  PathOption,
  QuickTransferSummaryState,
  QuickTransferSummaryAction,
  BlowOutLocation,
} from '../types'
import { ACTIONS } from '../constants'
import { i18n } from '../../../i18n'
import { InputField } from '../../../atoms/InputField'
import { NumericalKeyboard } from '../../../atoms/SoftwareKeyboard'

interface PipettePathProps {
  onBack: () => void
  state: QuickTransferSummaryState
  dispatch: React.Dispatch<QuickTransferSummaryAction>
}

export function PipettePath(props: PipettePathProps): JSX.Element {
  const { onBack, state, dispatch } = props
  const { t } = useTranslation('quick_transfer')
  const keyboardRef = React.useRef(null)
  const deckConfig = useNotifyDeckConfigurationQuery().data ?? []

  const [selectedPath, setSelectedPath] = React.useState<PathOption>(state.path)
  const [currentStep, setCurrentStep] = React.useState<number>(1)
  const [blowOutLocation, setBlowOutLocation] = React.useState<
    BlowOutLocation | undefined
  >(state.blowOut)

  const [disposalVolume, setDisposalVolume] = React.useState<number>(
    state.volume
  )
  const volumeLimits = getVolumeRange(state)

  const allowedPipettePathOptions: Array<{
    pathOption: PathOption
    description: string
  }> = [{ pathOption: 'single', description: t('pipette_path_single') }]
  if (
    state.transferType === 'distribute' &&
    volumeLimits.max >= state.volume * 3
  ) {
    // we have the capacity for a multi dispense if we can fit at least 2x the volume per well
    // for aspiration plus 1x the volume per well for disposal volume
    allowedPipettePathOptions.push({
      pathOption: 'multiDispense',
      description: t('pipette_path_multi_dispense'),
    })
    // for multi aspirate we only need at least 2x the volume per well
  } else if (
    state.transferType === 'consolidate' &&
    volumeLimits.max >= state.volume * 2
  ) {
    allowedPipettePathOptions.push({
      pathOption: 'multiAspirate',
      description: t('pipette_path_multi_aspirate'),
    })
  }

  const blowOutLocationItems = useBlowOutLocationOptions(
    deckConfig,
    state.transferType
  )

  const handleClickBackOrExit = (): void => {
    currentStep > 1 ? setCurrentStep(currentStep - 1) : onBack()
  }

  const handleClickSaveOrContinue = (): void => {
    if (currentStep === 1) {
      if (selectedPath !== 'multiDispense') {
        dispatch({
          type: ACTIONS.SET_PIPETTE_PATH,
          path: selectedPath,
        })
        onBack()
      } else {
        setCurrentStep(2)
      }
    } else if (currentStep === 2) {
      setCurrentStep(3)
    } else {
      dispatch({
        type: ACTIONS.SET_PIPETTE_PATH,
        path: selectedPath as PathOption,
        disposalVolume,
        blowOutLocation,
      })
      onBack()
    }
  }

  const saveOrContinueButtonText =
    selectedPath === 'multiDispense' && currentStep < 3
      ? t('shared:continue')
      : t('shared:save')

  const maxVolumeCapacity = volumeLimits.max - state.volume * 2
  const volumeRange = { min: 1, max: maxVolumeCapacity }

  const volumeError =
    disposalVolume !== null &&
    (disposalVolume < volumeRange.min || disposalVolume > volumeRange.max)
      ? t(`value_out_of_range`, {
          min: volumeRange.min,
          max: volumeRange.max,
        })
      : null

  let buttonIsDisabled = false
  if (currentStep === 2) {
    buttonIsDisabled = disposalVolume == null || volumeError != null
  } else if (currentStep === 3) {
    buttonIsDisabled = blowOutLocation == null
  }

  return createPortal(
    <Flex position={POSITION_FIXED} backgroundColor={COLORS.white} width="100%">
      <ChildNavigation
        header={t('pipette_path')}
        buttonText={i18n.format(saveOrContinueButtonText, 'capitalize')}
        onClickBack={handleClickBackOrExit}
        onClickButton={handleClickSaveOrContinue}
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
          {allowedPipettePathOptions.map(option => (
            <LargeButton
              key={option.pathOption}
              buttonType={
                selectedPath === option.pathOption ? 'primary' : 'secondary'
              }
              onClick={() => {
                setSelectedPath(option.pathOption)
              }}
              buttonText={option.description}
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
              value={disposalVolume}
              title={t('disposal_volume_µL')}
              error={volumeError}
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
                setDisposalVolume(Number(e))
              }}
            />
          </Flex>
        </Flex>
      ) : null}
      {currentStep === 3 ? (
        <Flex
          marginTop={SPACING.spacing120}
          flexDirection={DIRECTION_COLUMN}
          padding={`${SPACING.spacing16} ${SPACING.spacing60} ${SPACING.spacing40} ${SPACING.spacing60}`}
          gridGap={SPACING.spacing4}
          width="100%"
        >
          {blowOutLocationItems.map(option => (
            <LargeButton
              key={option.description}
              buttonType={
                blowOutLocation === option.location ? 'primary' : 'secondary'
              }
              onClick={() => {
                setBlowOutLocation(option.location)
              }}
              buttonText={option.description}
            />
          ))}
        </Flex>
      ) : null}
    </Flex>,
    getTopPortalEl()
  )
}
