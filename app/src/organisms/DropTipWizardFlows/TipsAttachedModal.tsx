import * as React from 'react'
import capitalize from 'lodash/capitalize'
import NiceModal, { useModal } from '@ebay/nice-modal-react'
import { Trans, useTranslation } from 'react-i18next'

import {
  COLORS,
  DIRECTION_COLUMN,
  Flex,
  SPACING,
  LegacyStyledText,
} from '@opentrons/components'
import { ApiHostProvider } from '@opentrons/react-api-client'
import { FLEX_ROBOT_TYPE } from '@opentrons/shared-data'

import { SmallButton } from '../../atoms/buttons'
import { OddModal } from '../../molecules/OddModal'
import { DropTipWizardFlows, useDropTipWizardFlows } from '.'

import type { HostConfig } from '@opentrons/api-client'
import type { OddModalHeaderBaseProps } from '../../molecules/OddModal/types'
import type { PipetteWithTip } from '.'

interface TipsAttachedModalProps {
  aPipetteWithTip: PipetteWithTip
  host: HostConfig | null
  setTipStatusResolved: (onEmpty?: () => void) => Promise<void>
}

export const handleTipsAttachedModal = (
  props: TipsAttachedModalProps
): Promise<unknown> => {
  return NiceModal.show(TipsAttachedModal, {
    ...props,
  })
}

const TipsAttachedModal = NiceModal.create(
  (props: TipsAttachedModalProps): JSX.Element => {
    const { aPipetteWithTip, host, setTipStatusResolved } = props
    const { t } = useTranslation(['drop_tip_wizard'])
    const modal = useModal()

    const { mount, specs } = aPipetteWithTip
    const { showDTWiz, toggleDTWiz } = useDropTipWizardFlows()

    const tipsAttachedHeader: OddModalHeaderBaseProps = {
      title: t('remove_any_attached_tips'),
      iconName: 'ot-alert',
      iconColor: COLORS.red50,
    }

    const cleanUpAndClose = (): void => {
      modal.remove()
      setTipStatusResolved()
    }

    const is96Channel = specs.channels === 96
    const displayMountText = is96Channel
      ? '96-Channel'
      : capitalize(mount as string)

    return (
      <ApiHostProvider {...host} hostname={host?.hostname ?? null}>
        <OddModal header={tipsAttachedHeader}>
          <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacing32}>
            <LegacyStyledText as="p">
              <Trans
                t={t}
                i18nKey="liquid_damages_this_pipette"
                values={{
                  mount: displayMountText,
                }}
                components={{
                  mount: <strong />,
                }}
              />
            </LegacyStyledText>
            <Flex gridGap={SPACING.spacing8}>
              <SmallButton
                flex="1"
                buttonType="secondary"
                buttonText={t('skip')}
                onClick={cleanUpAndClose}
              />
              <SmallButton
                flex="1"
                buttonText={t('begin_removal')}
                onClick={toggleDTWiz}
              />
            </Flex>
          </Flex>
        </OddModal>
        {showDTWiz ? (
          <DropTipWizardFlows
            instrumentModelSpecs={specs}
            mount={mount}
            robotType={FLEX_ROBOT_TYPE}
            closeFlow={() => {
              toggleDTWiz()
              cleanUpAndClose()
            }}
          />
        ) : null}
      </ApiHostProvider>
    )
  }
)
