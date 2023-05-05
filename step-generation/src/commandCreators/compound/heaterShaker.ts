import * as errorCreators from '../../errorCreators'
import { getModuleState } from '../../robotStateSelectors'
import {
  CommandCreator,
  CurriedCommandCreator,
  HeaterShakerArgs,
} from '../../types'
import { curryCommandCreator, reduceCommandCreators } from '../../utils'
import { delay } from '../atomic/delay'
import { heaterShakerCloseLatch } from '../atomic/heaterShakerCloseLatch'
import { heaterShakerDeactivateHeater } from '../atomic/heaterShakerDeactivateHeater'
import { heaterShakerOpenLatch } from '../atomic/heaterShakerOpenLatch'
import { heaterShakerSetTargetShakeSpeed } from '../atomic/heaterShakerSetTargetShakeSpeed'
import { heaterShakerStopShake } from '../atomic/heaterShakerStopShake'
import { setTemperature } from '../atomic/setTemperature'

export const heaterShaker: CommandCreator<HeaterShakerArgs> = (
  args,
  invariantContext,
  prevRobotState
) => {
  if (args.module == null) {
    return {
      errors: [errorCreators.missingModuleError()],
    }
  }
  const heaterShakerState = getModuleState(prevRobotState, args.module)

  if (heaterShakerState == null) {
    return {
      errors: [errorCreators.missingModuleError()],
    }
  }

  const commandCreators: CurriedCommandCreator[] = []

  if (args.latchOpen) {
    commandCreators.push(
      curryCommandCreator(heaterShakerOpenLatch, {
        moduleId: args.module,
      })
    )
  } else {
    commandCreators.push(
      curryCommandCreator(heaterShakerCloseLatch, {
        moduleId: args.module,
      })
    )
  }

  if (args.targetTemperature === null) {
    commandCreators.push(
      curryCommandCreator(heaterShakerDeactivateHeater, {
        moduleId: args.module,
      })
    )
  } else {
    commandCreators.push(
      curryCommandCreator(setTemperature, {
        module: args.module,
        targetTemperature: args.targetTemperature,
        commandCreatorFnName: 'setTemperature',
      })
    )
  }

  if (args.rpm === null) {
    commandCreators.push(
      curryCommandCreator(heaterShakerStopShake, {
        moduleId: args.module,
      })
    )
  } else {
    commandCreators.push(
      curryCommandCreator(heaterShakerSetTargetShakeSpeed, {
        moduleId: args.module,
        commandCreatorFnName: 'setShakeSpeed',
        rpm: args.rpm,
      })
    )
  }

  if (
    (args.timerMinutes != null && args.timerMinutes !== 0) ||
    (args.timerSeconds != null && args.timerSeconds !== 0)
  ) {
    const totalSeconds =
      (args.timerSeconds ?? 0) + (args.timerMinutes ?? 0) * 60
    commandCreators.push(
      curryCommandCreator(delay, {
        commandCreatorFnName: 'delay',
        description: null,
        name: null,
        meta: null,
        wait: totalSeconds,
      })
    )
    commandCreators.push(
      curryCommandCreator(heaterShakerStopShake, {
        moduleId: args.module,
      })
    )
    commandCreators.push(
      curryCommandCreator(heaterShakerDeactivateHeater, {
        moduleId: args.module,
      })
    )
  }

  return reduceCommandCreators(
    commandCreators,
    invariantContext,
    prevRobotState
  )
}
