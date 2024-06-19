import * as React from 'react'
import { describe, it, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'

import { renderWithProviders } from '../../../../__testing-utils__'
import {
  mockPickUpTipLabware,
  mockRecoveryContentProps,
} from '../../__fixtures__'
import { i18n } from '../../../../i18n'
import { LeftColumnLabwareInfo } from '../LeftColumnLabwareInfo'

const render = (props: React.ComponentProps<typeof LeftColumnLabwareInfo>) => {
  return renderWithProviders(<LeftColumnLabwareInfo {...props} />, {
    i18nInstance: i18n,
  })[0]
}

const mockTile = 'MOCK_TITLE'

describe('LeftColumnLabwareInfo', () => {
  let props: React.ComponentProps<typeof LeftColumnLabwareInfo>
  let mockFailedLabwareUtils: any

  beforeEach(() => {
    mockFailedLabwareUtils = {
      pickUpTipLabwareName: 'MOCK_LW_NAME',
      pickUpTipLabware: mockPickUpTipLabware,
    }

    props = {
      ...mockRecoveryContentProps,
      title: mockTile,
      failedLabwareUtils: mockFailedLabwareUtils,
      moveType: 'refill',
    }
  })

  it('renders appropriate copy', () => {
    render(props)

    screen.getByText('MOCK_TITLE')
    screen.getByText('MOCK_LW_NAME')
    screen.getByText('A1')
    screen.getByText(
      "It's best to replace tips and select the last location used for tip pickup."
    )
    screen.getByTestId('InlineNotification_alert')
  })
})