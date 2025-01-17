import * as React from 'react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor, renderHook } from '@testing-library/react'
import { createStore } from 'redux'

import { renderWithProviders } from '../../../__testing-utils__'
import { i18n } from '../../../i18n'
import { mockRecoveryContentProps } from '../__fixtures__'
import { getIsOnDevice } from '../../../redux/config'
import { useRunPausedSplash, RunPausedSplash } from '../RunPausedSplash'
import { StepInfo } from '../shared'

import type { Store } from 'redux'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Provider } from 'react-redux'

vi.mock('../../../redux/config')
vi.mock('../shared')

const store: Store<any> = createStore(vi.fn(), {})

describe('useRunPausedSplash', () => {
  let wrapper: React.FunctionComponent<{ children: React.ReactNode }>
  beforeEach(() => {
    vi.mocked(getIsOnDevice).mockReturnValue(true)
    const queryClient = new QueryClient()
    wrapper = ({ children }) => (
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Provider>
    )
  })

  const TEST_CASES = [
    { isOnDevice: true, showERWizard: true, expected: true },
    { isOnDevice: true, showERWizard: false, expected: true },
    { isOnDevice: false, showERWizard: true, expected: false },
    { isOnDevice: false, showERWizard: false, expected: true },
  ]

  describe('useRunPausedSplash', () => {
    TEST_CASES.forEach(({ isOnDevice, showERWizard, expected }) => {
      it(`returns ${expected} when isOnDevice is ${isOnDevice} and showERWizard is ${showERWizard}`, () => {
        const { result } = renderHook(
          () => useRunPausedSplash(isOnDevice, showERWizard),
          {
            wrapper,
          }
        )
        expect(result.current).toEqual(expected)
      })
    })
  })
})

const render = (props: React.ComponentProps<typeof RunPausedSplash>) => {
  return renderWithProviders(
    <MemoryRouter>
      <RunPausedSplash {...props} />
    </MemoryRouter>,
    {
      i18nInstance: i18n,
    }
  )
}

describe('RunPausedSplash', () => {
  let props: React.ComponentProps<typeof RunPausedSplash>
  const mockToggleERWiz = vi.fn(() => Promise.resolve())
  const mockProceedToRouteAndStep = vi.fn()
  const mockRouteUpdateActions = {
    proceedToRouteAndStep: mockProceedToRouteAndStep,
  } as any

  beforeEach(() => {
    props = {
      ...mockRecoveryContentProps,
      robotName: 'testRobot',
      toggleERWizAsActiveUser: mockToggleERWiz,
      routeUpdateActions: mockRouteUpdateActions,
    }

    vi.mocked(StepInfo).mockReturnValue(<div>MOCK STEP INFO</div>)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render a generic paused screen if there is no handled errorType', () => {
    render(props)
    screen.getByText('Error')
    screen.getByText('MOCK STEP INFO')
  })

  it('should render an overpressure error type if the errorType is overpressure', () => {
    props = {
      ...props,
      failedCommand: {
        ...props.failedCommand,
        commandType: 'aspirate',
        error: { isDefined: true, errorType: 'overpressure' },
      } as any,
    }
    render(props)
    screen.getByText('Pipette overpressure')
    screen.getByText('MOCK STEP INFO')
  })

  it('should contain buttons with expected appearance and behavior', async () => {
    render(props)

    const primaryBtn = screen.getByRole('button', {
      name: 'Launch Recovery Mode',
    })
    const secondaryBtn = screen.getByRole('button', { name: 'Cancel run' })

    expect(primaryBtn).toBeInTheDocument()
    expect(secondaryBtn).toBeInTheDocument()

    fireEvent.click(secondaryBtn)

    await waitFor(() => {
      expect(mockToggleERWiz).toHaveBeenCalledTimes(1)
    })
    await waitFor(() => {
      expect(mockToggleERWiz).toHaveBeenCalledWith(true, false)
    })
    await waitFor(() => {
      expect(mockProceedToRouteAndStep).toHaveBeenCalledTimes(1)
    })

    expect(mockToggleERWiz.mock.invocationCallOrder[0]).toBeLessThan(
      mockProceedToRouteAndStep.mock.invocationCallOrder[0]
    )

    fireEvent.click(primaryBtn)
    await waitFor(() => {
      expect(mockToggleERWiz).toHaveBeenCalledTimes(2)
    })
    await waitFor(() => {
      expect(mockToggleERWiz).toHaveBeenCalledWith(true, true)
    })
  })
})
