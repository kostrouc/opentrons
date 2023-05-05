import * as React from 'react'
import { renderHook } from '@testing-library/react-hooks'
import { resetAllWhenMocks } from 'jest-when'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Provider } from 'react-redux'
import { createStore, Store } from 'redux'

import { useSyncRobotClock } from '..'
import { syncSystemTime } from '../../../../redux/robot-admin'

jest.mock('../../../../redux/discovery')

const store: Store<any> = createStore(jest.fn(), {})

describe('useSyncRobotClock hook', () => {
  let wrapper: React.FunctionComponent<{}>
  beforeEach(() => {
    store.dispatch = jest.fn()
    const queryClient = new QueryClient()
    wrapper = ({ children }) => (
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Provider>
    )
  })
  afterEach(() => {
    resetAllWhenMocks()
    jest.resetAllMocks()
  })

  it('dispatches action to sync robot system time on mount and then not again on subsequent renders', () => {
    const { rerender } = renderHook(() => useSyncRobotClock('otie'), {
      wrapper,
    })

    expect(store.dispatch).toHaveBeenCalledWith(syncSystemTime('otie'))
    rerender()
    expect(store.dispatch).toHaveBeenCalledTimes(1)
  })
})
