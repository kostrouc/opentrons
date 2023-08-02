import { mockRobot } from '../../robot-api/__fixtures__'
import { INITIAL_STATE, robotUpdateReducer } from '../reducer'
import type { Action } from '../../types'
import type { RobotUpdateState } from '../types'

const BASE_SESSION = {
  robotName: mockRobot.name,
  userFileInfo: null,
  step: null,
  token: null,
  pathPrefix: null,
  stage: null,
  progress: null,
  error: null,
}

describe('robot update reducer', () => {
  const SPECS = [
    {
      name: 'handles robotUpdate:UPDATE_INFO',
      action: {
        type: 'robotUpdate:UPDATE_INFO',
        payload: { version: '1.0.0', releaseNotes: 'release notes' },
      },
      initialState: { ...INITIAL_STATE, info: null },
      expected: {
        ...INITIAL_STATE,
        info: { version: '1.0.0', releaseNotes: 'release notes' },
      },
    },
    {
      name: 'handles robotUpdate:USER_FILE_INFO',
      action: {
        type: 'robotUpdate:USER_FILE_INFO',
        payload: {
          systemFile: '/path/to/system.zip',
          version: '1.0.0',
          releaseNotes: 'release notes',
        },
      },
      initialState: {
        ...INITIAL_STATE,
        session: { robotName: mockRobot.name },
      },
      expected: {
        ...INITIAL_STATE,
        session: {
          robotName: mockRobot.name,
          userFileInfo: {
            systemFile: '/path/to/system.zip',
            version: '1.0.0',
            releaseNotes: 'release notes',
          },
        },
      },
    },
    {
      name: 'handles robotUpdate:SET_UPDATE_SEEN',
      action: { type: 'robotUpdate:SET_UPDATE_SEEN' },
      initialState: { ...INITIAL_STATE, seen: false },
      expected: { ...INITIAL_STATE, seen: true },
    },
    {
      name: 'handles robotUpdate:DOWNLOAD_PROGRESS',
      action: { type: 'robotUpdate:DOWNLOAD_PROGRESS', payload: 42 },
      initialState: { ...INITIAL_STATE, downloadProgress: null },
      expected: { ...INITIAL_STATE, downloadProgress: 42 },
    },
    {
      name: 'handles robotUpdate:DOWNLOAD_ERROR',
      action: { type: 'robotUpdate:DOWNLOAD_ERROR', payload: 'AH' },
      initialState: { ...INITIAL_STATE, downloadError: null },
      expected: { ...INITIAL_STATE, downloadError: 'AH' },
    },
    {
      name: 'handles robotUpdate:START_UPDATE',
      action: {
        type: 'robotUpdate:START_UPDATE',
        payload: { robotName: mockRobot.name },
      },
      initialState: { ...INITIAL_STATE, session: null },
      expected: { ...INITIAL_STATE, session: BASE_SESSION },
    },
    {
      name: 'robotUpdate:START_UPDATE preserves user file info',
      action: {
        type: 'robotUpdate:START_UPDATE',
        payload: { robotName: mockRobot.name },
      },
      initialState: {
        ...INITIAL_STATE,
        session: {
          ...BASE_SESSION,
          robotName: mockRobot.name,
          userFileInfo: { systemFile: 'system.zip' },
        },
      },
      expected: {
        ...INITIAL_STATE,
        session: {
          ...BASE_SESSION,
          robotName: mockRobot.name,
          userFileInfo: { systemFile: 'system.zip' },
        },
      },
    },
    {
      name: 'handles robotUpdate:START_PREMIGRATION',
      action: {
        type: 'robotUpdate:START_PREMIGRATION',
        payload: { name: mockRobot.name, ip: '10.10.0.0', port: 31950 },
      },
      initialState: { ...INITIAL_STATE, session: BASE_SESSION },
      expected: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, step: 'premigration' },
      },
    },
    {
      name: 'handles robotUpdate:PREMIGRATION_DONE',
      action: { type: 'robotUpdate:PREMIGRATION_DONE' },
      initialState: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, step: 'premigration' },
      },
      expected: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, step: 'premigrationRestart' },
      },
    },
    {
      name: 'handles robotUpdate:CREATE_SESSION',
      action: {
        type: 'robotUpdate:CREATE_SESSION',
        payload: { host: mockRobot, sessionPath: '/session/update/begin' },
      },
      initialState: { ...INITIAL_STATE, session: BASE_SESSION },
      expected: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, step: 'getToken' },
      },
    },
    {
      name: 'handles robotUpdate:CREATE_SESSION_SUCCESS',
      action: {
        type: 'robotUpdate:CREATE_SESSION_SUCCESS',
        payload: {
          host: mockRobot,
          pathPrefix: '/session/update',
          token: 'foobar',
        },
      },
      initialState: {
        ...INITIAL_STATE,
        session: {
          ...BASE_SESSION,
          step: 'getToken',
        },
      },
      expected: {
        ...INITIAL_STATE,
        session: {
          ...BASE_SESSION,
          step: 'getToken',
          pathPrefix: '/session/update',
          token: 'foobar',
        },
      },
    },
    {
      name: 'handles robotUpdate:STATUS',
      action: {
        type: 'robotUpdate:STATUS',
        payload: { stage: 'writing', progress: 10, message: 'Writing file' },
      },
      initialState: { ...INITIAL_STATE, session: BASE_SESSION },
      expected: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, stage: 'writing', progress: 10 },
      },
    },
    {
      name: 'handles robotUpdate:STATUS with error',
      action: {
        type: 'robotUpdate:STATUS',
        payload: { stage: 'error', error: 'error-type', message: 'AH!' },
      },
      initialState: { ...INITIAL_STATE, session: BASE_SESSION },
      expected: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, stage: 'error', error: 'AH!' },
      },
    },
    {
      name: 'handles robotUpdate:UPLOAD_FILE',
      action: {
        type: 'robotUpdate:UPLOAD_FILE',
        payload: {
          host: { name: mockRobot.name },
          path: '/server/update/a-token/file',
        },
        meta: { shell: true },
      },
      initialState: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, step: 'getToken' },
      },
      expected: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, step: 'uploadFile' },
      },
    },
    {
      name: 'handles robotUpdate:FILE_UPLOAD_DONE',
      action: { type: 'robotUpdate:FILE_UPLOAD_DONE' },
      initialState: {
        ...INITIAL_STATE,
        session: {
          ...BASE_SESSION,
          step: 'uploadFile',
        },
      },
      expected: {
        ...INITIAL_STATE,
        session: {
          ...BASE_SESSION,
          step: 'processFile',
        },
      },
    },
    {
      name: 'handles robotUpdate:CLEAR_SESSION',
      action: { type: 'robotUpdate:CLEAR_SESSION' },
      initialState: { ...INITIAL_STATE, session: BASE_SESSION },
      expected: { ...INITIAL_STATE, session: null },
    },
    {
      name: 'handles robotUpdate:UNEXPECTED_ERROR',
      action: {
        type: 'robotUpdate:UNEXPECTED_ERROR',
        payload: { message: 'AH!' },
      },
      initialState: { ...INITIAL_STATE, session: BASE_SESSION },
      expected: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, error: 'AH!' },
      },
    },
    {
      name: 'handles robotUpdate:PREMIGRATION_ERROR',
      action: {
        type: 'robotUpdate:PREMIGRATION_ERROR',
        payload: { message: 'AH!' },
      },
      initialState: { ...INITIAL_STATE, session: BASE_SESSION },
      expected: {
        ...INITIAL_STATE,
        session: { ...BASE_SESSION, error: 'AH!' },
      },
    },
  ]

  SPECS.forEach(spec => {
    const { name, action, initialState, expected } = spec
    it(name, () =>
      expect(
        robotUpdateReducer(initialState as RobotUpdatesState, action as Action)
      ).toEqual(expected)
    )
  })
})
