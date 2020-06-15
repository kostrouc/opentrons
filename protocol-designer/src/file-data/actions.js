// @flow
import type { Timeline } from '../step-generation'
import type { FileMetadataFields, SaveFileMetadataAction } from './types'

export const saveFileMetadata = (
  payload: FileMetadataFields
): SaveFileMetadataAction => ({
  type: 'SAVE_FILE_METADATA',
  payload,
})

export type ComputeRobotStateTimelineRequestAction = {|
  type: 'GET_ROBOT_STATE_TIMELINE_REQUEST',
|}
export const computeRobotStateTimelineRequest = (): ComputeRobotStateTimelineRequestAction => ({
  type: 'GET_ROBOT_STATE_TIMELINE_REQUEST',
})

export type ComputeRobotStateTimelineSuccessAction = {|
  type: 'GET_ROBOT_STATE_TIMELINE_SUCCESS',
  payload: Timeline,
|}
export const computeRobotStateTimelineSuccess = (
  payload: $PropertyType<ComputeRobotStateTimelineSuccessAction, 'payload'>
): ComputeRobotStateTimelineSuccessAction => ({
  type: 'GET_ROBOT_STATE_TIMELINE_SUCCESS',
  payload,
})
