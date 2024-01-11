import * as React from 'react'
import styled, { css } from 'styled-components'
import {
  TYPOGRAPHY,
  LEGACY_COLORS,
  SPACING,
  BORDERS,
  COLORS,
  Flex,
  RESPONSIVENESS,
} from '@opentrons/components'
import { StyledText } from '../text'

import type { StyleProps } from '@opentrons/components'

interface RadioButtonProps extends StyleProps {
  buttonLabel: string
  buttonValue: string | number
  onChange: React.ChangeEventHandler<HTMLInputElement>
  disabled?: boolean
  isSelected?: boolean
  radioButtonType?: 'large' | 'small'
  subButtonLabel?: string
}

export function RadioButton(props: RadioButtonProps): JSX.Element {
  const {
    buttonLabel,
    buttonValue,
    disabled = false,
    isSelected = false,
    onChange,
    radioButtonType = 'large',
    subButtonLabel,
  } = props

  const isLarge = radioButtonType === 'large'

  const SettingButton = styled.input`
    display: none;
  `

  const AVAILABLE_BUTTON_STYLE = css`
    background: ${COLORS.blue35};

    &:active {
      background-color: ${COLORS.blue40};
    }
  `

  const SELECTED_BUTTON_STYLE = css`
    background: ${COLORS.blue50};
    color: ${LEGACY_COLORS.white};

    &:active {
      background-color: ${COLORS.blue60};
    }
  `

  const DISABLED_BUTTON_STYLE = css`
    background-color: ${LEGACY_COLORS.darkBlack20};
    color: ${LEGACY_COLORS.darkBlack60};
    cursor: not-allowed;
  `

  // TODO: (ew, 2023-04-21): button is not tabbable, so focus state
  // is not possible on ODD. It's testable in storybook but not in real life.
  const SettingButtonLabel = styled.label`
    border-radius: ${BORDERS.borderRadiusSize4};
    cursor: pointer;
    padding: ${isLarge ? SPACING.spacing24 : SPACING.spacing20};
    width: 100%;

    ${isSelected ? SELECTED_BUTTON_STYLE : AVAILABLE_BUTTON_STYLE}
    ${disabled && DISABLED_BUTTON_STYLE}

    @media ${RESPONSIVENESS.touchscreenMediaQuerySpecs} {
      cursor: default;
    }
  `

  return (
    <Flex width="100%">
      <SettingButton
        checked={isSelected}
        disabled={disabled}
        id={buttonLabel}
        onChange={onChange}
        type="radio"
        value={buttonValue}
      />
      <SettingButtonLabel role="label" htmlFor={buttonLabel}>
        <StyledText
          fontSize={isLarge ? TYPOGRAPHY.fontSize28 : TYPOGRAPHY.fontSize22}
          fontWeight={TYPOGRAPHY.fontWeightSemiBold}
          lineHeight={
            isLarge ? TYPOGRAPHY.lineHeight36 : TYPOGRAPHY.lineHeight28
          }
        >
          {buttonLabel}
        </StyledText>
        {subButtonLabel != null ? (
          <StyledText as="h4" fontWeight={TYPOGRAPHY.fontWeightRegular}>
            {subButtonLabel}
          </StyledText>
        ) : null}
      </SettingButtonLabel>
    </Flex>
  )
}
