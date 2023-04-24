export const longCommandMessage =
  'This is a user generated message that gives details about the pause command. This text is truncated to 220 characters. semper risus in hendrerit gravida rutrum quisque non tellus orci ac auctor augue mauris augue neque gravida in fermentum et sollicitudin ac orci phasellus egestas tellus rutrum tellus pellentesque'

export const truncatedCommandMessage =
  'This is a user generated message that gives details about the pause command. This text is truncated to 220 characters. semper risus in hendrerit gravida rutrum quisque non tellus orci ac auctor augue mauris augue nequ...'

export const shortCommandMessage =
  "this won't get truncated because it isn't more than 220 characters."

export const MOCK_LABWARE_ID = '71e1664f-3e69-400a-931b-1ddfa3bff5c8'
export const MOCK_MODULE_ID = 'f806ff9f-3b17-4692-aa63-f77c57fe18d1'

export const mockPauseCommandWithStartTime = {
  commandType: 'waitForResume',
  params: {
    startedAt: new Date(),
    message: longCommandMessage,
  },
} as any

export const mockPauseCommandWithoutStartTime = {
  commandType: 'waitForResume',
  params: {
    startedAt: null,
    message: longCommandMessage,
  },
} as any

export const mockPauseCommandWithShortMessage = {
  commandType: 'waitForResume',
  params: {
    startedAt: null,
    message: shortCommandMessage,
  },
} as any

export const mockPauseCommandWithNoMessage = {
  commandType: 'waitForResume',
  params: {
    startedAt: null,
    message: null,
  },
} as any

export const mockMoveLabwareCommand = {
  commandType: 'moveLabware',
  params: {
    labwareId: MOCK_LABWARE_ID,
    newLocation: {
      slotName: '5',
    },
    strategy: 'manualMoveWithPause',
  },
} as any
