import * as React from 'react'
import i18n from 'i18next'
import { waitFor } from '@testing-library/react'
import { WASTE_CHUTE_CUTOUT } from '@opentrons/shared-data'
import { renderWithProviders } from '@opentrons/components'

import { getInitialDeckSetup } from '../../../step-forms/selectors'
import { getSlotIsEmpty } from '../../../step-forms'
import {
  createDeckFixture,
  deleteDeckFixture,
} from '../../../step-forms/actions/additionalItems'
import { TrashModal } from '../TrashModal'

jest.mock('../../../step-forms')
jest.mock('../../../step-forms/selectors')
jest.mock('../../../step-forms/actions/additionalItems')

const mockGetInitialDeckSetup = getInitialDeckSetup as jest.MockedFunction<
  typeof getInitialDeckSetup
>
const mockGetSlotIsEmpty = getSlotIsEmpty as jest.MockedFunction<
  typeof getSlotIsEmpty
>
const mockCreateDeckFixture = createDeckFixture as jest.MockedFunction<
  typeof createDeckFixture
>
const mockDeleteDeckFixture = deleteDeckFixture as jest.MockedFunction<
  typeof deleteDeckFixture
>
const render = (props: React.ComponentProps<typeof TrashModal>) => {
  return renderWithProviders(<TrashModal {...props} />, {
    i18nInstance: i18n,
  })[0]
}

describe('TrashModal ', () => {
  let props: React.ComponentProps<typeof TrashModal>
  beforeEach(() => {
    props = {
      onCloseClick: jest.fn(),
      trashName: 'trashBin',
    }
    mockGetInitialDeckSetup.mockReturnValue({
      pipettes: {},
      additionalEquipmentOnDeck: {},
      labware: {},
      modules: {},
    })
    mockGetSlotIsEmpty.mockReturnValue(true)
  })
  it('renders buttons, position and slot dropdown', async () => {
    const { getByRole, getByText } = render(props)
    getByText('Trash Bin')
    getByText('Position')
    getByText('Slot A1')
    getByText('Slot A3')
    getByText('Slot B1')
    getByText('Slot B3')
    getByText('Slot C1')
    getByText('Slot C3')
    getByText('Slot D1')
    getByText('Slot D3')
    getByRole('button', { name: 'cancel' }).click()
    expect(props.onCloseClick).toHaveBeenCalled()
    getByRole('button', { name: 'save' }).click()
    await waitFor(() => {
      expect(mockCreateDeckFixture).toHaveBeenCalledWith('trashBin', 'cutoutA3')
    })
  })
  it('call delete then create container when trash is already on the slot', async () => {
    const mockId = 'mockTrashId'
    props = {
      ...props,
      trashBinId: mockId,
    }
    const { getByRole, getByText } = render(props)
    getByText('Trash Bin')
    getByRole('button', { name: 'save' }).click()
    await waitFor(() => {
      expect(mockDeleteDeckFixture).toHaveBeenCalledWith(mockId)
      expect(mockCreateDeckFixture).toHaveBeenCalledWith('trashBin', 'cutoutA3')
    })
  })
  it('renders the button as disabled when the slot is full for trash bin', () => {
    mockGetSlotIsEmpty.mockReturnValue(false)
    const { getByRole } = render(props)
    expect(getByRole('button', { name: 'save' })).toBeDisabled()
  })
  it('renders buttons for waste chute', async () => {
    props = {
      ...props,
      trashName: 'wasteChute',
    }
    const { getByRole, getByText } = render(props)
    getByText('Waste Chute')
    getByRole('button', { name: 'cancel' }).click()
    expect(props.onCloseClick).toHaveBeenCalled()
    getByRole('button', { name: 'save' }).click()
    await waitFor(() => {
      expect(mockCreateDeckFixture).toHaveBeenCalledWith(
        'wasteChute',
        WASTE_CHUTE_CUTOUT
      )
    })
  })
  it('renders the button as disabled when the slot is full for waste chute', () => {
    props = {
      ...props,
      trashName: 'wasteChute',
    }
    mockGetSlotIsEmpty.mockReturnValue(false)
    const { getByRole } = render(props)
    expect(getByRole('button', { name: 'save' })).toBeDisabled()
  })
})
