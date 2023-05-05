import styled from 'styled-components'

import { NewAlertPrimaryBtn, styleProps } from '../../primitives'
import { COLORS, BORDERS, TYPOGRAPHY, SPACING } from '../../ui-style-constants'

export const AlertPrimaryButton = styled(NewAlertPrimaryBtn)`
  background-color: ${COLORS.errorEnabled};
  border-radius: ${BORDERS.radiusSoftCorners};
  padding-left: ${SPACING.spacing4};
  padding-right: ${SPACING.spacing4};
  text-transform: ${TYPOGRAPHY.textTransformNone};
  box-shadow: 0 0 0;
  ${TYPOGRAPHY.pSemiBold}

  ${styleProps}

  &:hover {
    box-shadow: 0 0 0;
  }

  &:disabled {
    background-color: ${COLORS.darkGreyDisabled};
    color: ${COLORS.errorDisabled};
  }
`
