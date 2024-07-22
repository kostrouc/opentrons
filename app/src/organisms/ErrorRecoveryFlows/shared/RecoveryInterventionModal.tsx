import * as React from 'react'
import { createPortal } from 'react-dom'
import { css } from 'styled-components'

import { Flex, RESPONSIVENESS, SPACING } from '@opentrons/components'

import { InterventionModal } from '../../../molecules/InterventionModal'
import { getModalPortalEl, getTopPortalEl } from '../../../App/portal'

import type { ModalType } from '../../../molecules/InterventionModal'

export type RecoveryInterventionModalProps = Omit<
  React.ComponentProps<typeof InterventionModal>,
  'type'
> & {
  /* If on desktop, specifies the hard-coded dimensions height of the modal. */
  desktopType: 'desktop-small' | 'desktop-large'
  isOnDevice: boolean
}

// A wrapper around InterventionModal with Error-Recovery specific props and styling.
export function RecoveryInterventionModal({
  children,
  desktopType,
  isOnDevice,
  ...rest
}: RecoveryInterventionModalProps): JSX.Element {
  const restProps = {
    ...rest,
    type: 'error' as ModalType,
  }

  return createPortal(
    <InterventionModal {...restProps}>
      <Flex
        css={
          desktopType === 'desktop-small'
            ? SMALL_MODAL_STYLE
            : LARGE_MODAL_STYLE
        }
        padding={SPACING.spacing32}
      >
        {children}
      </Flex>
    </InterventionModal>,
    isOnDevice ? getTopPortalEl() : getModalPortalEl()
  )
}

const ODD_STYLE = `
@media ${RESPONSIVENESS.touchscreenMediaQuerySpecs} {
    height: 100%;
  }
`

const SMALL_MODAL_STYLE = css`
  height: 22rem;
  ${ODD_STYLE}
`
const LARGE_MODAL_STYLE = css`
  height: 26.75rem;
  ${ODD_STYLE}
`