import * as React from 'react'
import { vi, it, describe, expect, beforeEach, afterEach } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'
import { when } from 'vitest-when'
import { Route, MemoryRouter, Routes } from 'react-router-dom'
import '@testing-library/jest-dom/vitest'
import { renderWithProviders } from '../../../__testing-utils__'
import {
  useCreateRunMutation,
  useHost,
  useProtocolQuery,
  useProtocolAnalysisAsDocumentQuery,
} from '@opentrons/react-api-client'
import { i18n } from '../../../i18n'
import { useHardwareStatusText } from '../../../organisms/OnDeviceDisplay/RobotDashboard/hooks'
import { useOffsetCandidatesForAnalysis } from '../../../organisms/ApplyHistoricOffsets/hooks/useOffsetCandidatesForAnalysis'
import { useMissingProtocolHardware } from '../../Protocols/hooks'
import { formatTimeWithUtcLabel } from '../../../resources/runs'
import { DeleteTransferConfirmationModal } from '../../QuickTransferDashboard/DeleteTransferConfirmationModal'
import { QuickTransferDetails } from '..'
import { Deck } from '../Deck'
import { Hardware } from '../Hardware'
import { Labware } from '../Labware'

import type { HostConfig } from '@opentrons/api-client'

// Mock IntersectionObserver
class IntersectionObserver {
  observe = vi.fn()
  disconnect = vi.fn()
  unobserve = vi.fn()
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: IntersectionObserver,
})
vi.mock('../../../organisms/ProtocolSetupParameters')
vi.mock('@opentrons/api-client')
vi.mock('@opentrons/react-api-client')
vi.mock('../../../organisms/OnDeviceDisplay/RobotDashboard/hooks')
vi.mock(
  '../../../organisms/ApplyHistoricOffsets/hooks/useOffsetCandidatesForAnalysis'
)
vi.mock('../../QuickTransferDashboard/DeleteTransferConfirmationModal')
vi.mock('../../Protocols/hooks')
vi.mock('../Deck')
vi.mock('../Hardware')
vi.mock('../Labware')
vi.mock('../../../redux/config')

const MOCK_HOST_CONFIG = {} as HostConfig
const mockCreateRun = vi.fn((id: string) => {})
const MOCK_DATA = {
  data: {
    id: 'fakeTransferId',
    createdAt: '2022-05-03T21:36:12.494778+00:00',
    protocolType: 'json',
    metadata: {
      protocolName:
        'Nextera XT DNA Library Prep Kit Protocol: Part 1/4 - Tagment Genomic DNA and Amplify Libraries',
      author: 'engineering testing division',
      description: 'A short mock quick transfer',
      created: 1606853851893,
      tags: ['unitTest'],
    },
    analysisSummaries: [],
    files: [],
    key: '26ed5a82-502f-4074-8981-57cdda1d066d',
  },
}

const render = (path = '/quick-transfer/fakeTransferId') => {
  return renderWithProviders(
    <MemoryRouter initialEntries={[path]} initialIndex={0}>
      <Routes>
        <Route
          path="/quick-transfer/:transferId"
          element={<QuickTransferDetails />}
        />
      </Routes>
    </MemoryRouter>,
    {
      i18nInstance: i18n,
    }
  )
}

describe('ODDQuickTransferDetails', () => {
  beforeEach(() => {
    vi.mocked(useCreateRunMutation).mockReturnValue({
      createRun: mockCreateRun,
    } as any)
    vi.mocked(useOffsetCandidatesForAnalysis).mockReturnValue([])
    vi.mocked(useProtocolQuery).mockReturnValue({
      data: MOCK_DATA,
      isLoading: false,
    } as any)
    vi.mocked(useHardwareStatusText).mockReturnValue(
      'mock missing hardware chip text'
    )
    vi.mocked(useMissingProtocolHardware).mockReturnValue({
      missingProtocolHardware: [],
      isLoading: false,
      conflictedSlots: [],
    })
    vi.mocked(useProtocolAnalysisAsDocumentQuery).mockReturnValue({
      data: {
        id: 'mockAnalysisId',
        status: 'completed',
      },
    } as any)
    when(vi.mocked(useHost)).calledWith().thenReturn(MOCK_HOST_CONFIG)
  })
  afterEach(() => {
    vi.resetAllMocks()
  })

  it('renders transfer truncated name that expands when clicked', () => {
    render()
    const name = screen.getByText(
      'Nextera XT DNA Library Prep Kit Protocol: Part 1/4 - Tagment...Amplify Libraries'
    )
    fireEvent.click(name)
    screen.getByText(
      'Nextera XT DNA Library Prep Kit Protocol: Part 1/4 - Tagment Genomic DNA and Amplify Libraries'
    )
  })

  it('renders the start setup button', () => {
    render()
    screen.getByText('Start setup')
  })

  it('renders the transfer description', () => {
    render()
    screen.getByText('A short mock quick transfer')
  })

  it('renders the transfer date added', () => {
    render()
    screen.getByText(
      `Date Added: ${formatTimeWithUtcLabel(
        '2022-05-03T21:36:12.494778+00:00'
      )}`
    )
  })

  it('renders the pin transfer button', () => {
    render()
    screen.getByText('Pin quick transfer')
  })

  it('renders the delete quick transfer button', async () => {
    render()
    const deleteButton = screen.getByRole('button', {
      name: 'Delete quick transfer',
    })
    fireEvent.click(deleteButton)
    expect(vi.mocked(DeleteTransferConfirmationModal)).toHaveBeenCalled()
  })

  it('renders the navigation buttons', () => {
    vi.mocked(Hardware).mockReturnValue(<div>Mock Hardware</div>)
    vi.mocked(Labware).mockReturnValue(<div>Mock Labware</div>)
    vi.mocked(Deck).mockReturnValue(<div>Mock Initial Deck Layout</div>)

    render()
    const hardwareButton = screen.getByRole('button', { name: 'Hardware' })
    fireEvent.click(hardwareButton)
    screen.getByText('Mock Hardware')
    const labwareButton = screen.getByRole('button', { name: 'Labware' })
    fireEvent.click(labwareButton)
    screen.getByText('Mock Labware')
    const deckButton = screen.getByRole('button', { name: 'Deck' })
    fireEvent.click(deckButton)
    screen.getByText('Mock Initial Deck Layout')
    const summaryButton = screen.getByRole('button', { name: 'Summary' })
    fireEvent.click(summaryButton)
    screen.getByText('A short mock quick transfer')
  })

  it('should render a loading skeleton while awaiting a response from the server', () => {
    vi.mocked(useProtocolQuery).mockReturnValue({
      data: MOCK_DATA,
      isLoading: true,
    } as any)
    render()
    expect(screen.getAllByTestId('Skeleton').length).toBeGreaterThan(0)
  })

  it('render chip about modules when missing a hardware', () => {
    vi.mocked(useProtocolAnalysisAsDocumentQuery).mockReturnValue({
      data: {
        id: 'mockAnalysisId',
        status: 'completed',
      },
    } as any)
    render()
    screen.getByText('mock missing hardware chip text')
  })
})
