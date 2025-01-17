import * as React from 'react'
import { Trans, useTranslation } from 'react-i18next'

import {
  DIRECTION_COLUMN,
  COLORS,
  SPACING,
  Flex,
  StyledText,
  ALIGN_CENTER,
  Icon,
} from '@opentrons/components'

import {
  RECOVERY_MAP,
  FLEX_WIDTH_ALERT_INFO_STYLE,
  ICON_SIZE_ALERT_INFO_STYLE,
} from '../constants'
import {
  RecoveryFooterButtons,
  RecoverySingleColumnContentWrapper,
} from '../shared'
import { DropTipWizardFlows } from '../../DropTipWizardFlows'
import { DT_ROUTES } from '../../DropTipWizardFlows/constants'
import { SelectRecoveryOption } from './SelectRecoveryOption'

import type { PipetteWithTip } from '../../DropTipWizardFlows'
import type { RecoveryContentProps, RecoveryRoute, RouteStep } from '../types'
import type { FixitCommandTypeUtils } from '../../DropTipWizardFlows/types'

// The Drop Tip flow entry point. Includes entry from SelectRecoveryOption and CancelRun.
export function ManageTips(props: RecoveryContentProps): JSX.Element {
  const { recoveryMap } = props

  const buildContent = (): JSX.Element => {
    const { DROP_TIP_FLOWS } = RECOVERY_MAP
    const { step, route } = recoveryMap

    switch (step) {
      case DROP_TIP_FLOWS.STEPS.BEGIN_REMOVAL:
        return <BeginRemoval {...props} />
      case DROP_TIP_FLOWS.STEPS.BEFORE_BEGINNING:
      case DROP_TIP_FLOWS.STEPS.CHOOSE_BLOWOUT:
      case DROP_TIP_FLOWS.STEPS.CHOOSE_TIP_DROP:
        return <DropTipFlowsContainer {...props} />
      default:
        console.warn(`${step} in ${route} not explicitly handled. Rerouting.`)
        return <SelectRecoveryOption {...props} />
    }
  }

  return buildContent()
}

export function BeginRemoval({
  tipStatusUtils,
  routeUpdateActions,
  recoveryCommands,
  currentRecoveryOptionUtils,
}: RecoveryContentProps): JSX.Element | null {
  const { t } = useTranslation('error_recovery')
  const { aPipetteWithTip } = tipStatusUtils
  const {
    proceedNextStep,
    setRobotInMotion,
    proceedToRouteAndStep,
  } = routeUpdateActions
  const { cancelRun } = recoveryCommands
  const { selectedRecoveryOption } = currentRecoveryOptionUtils
  const { ROBOT_CANCELING, RETRY_NEW_TIPS } = RECOVERY_MAP
  const mount = aPipetteWithTip?.mount

  const primaryOnClick = (): void => {
    void proceedNextStep()
  }

  const secondaryOnClick = (): void => {
    if (selectedRecoveryOption === RETRY_NEW_TIPS.ROUTE) {
      void proceedToRouteAndStep(
        RETRY_NEW_TIPS.ROUTE,
        RETRY_NEW_TIPS.STEPS.REPLACE_TIPS
      )
    } else {
      void setRobotInMotion(true, ROBOT_CANCELING.ROUTE).then(() => {
        cancelRun()
      })
    }
  }

  return (
    <RecoverySingleColumnContentWrapper
      gridGap={SPACING.spacing24}
      alignItems={ALIGN_CENTER}
    >
      <Flex
        flexDirection={DIRECTION_COLUMN}
        alignItems={ALIGN_CENTER}
        gridGap={SPACING.spacing16}
        padding={`${SPACING.spacing32} ${SPACING.spacing16}`}
        height="100%"
        css={FLEX_WIDTH_ALERT_INFO_STYLE}
      >
        <Icon
          name="ot-alert"
          css={ICON_SIZE_ALERT_INFO_STYLE}
          marginTop={SPACING.spacing24}
          color={COLORS.red50}
        />
        <StyledText oddStyle="level3HeaderBold" desktopStyle="headingSmallBold">
          {t('remove_any_attached_tips')}
        </StyledText>
        <StyledText
          oddStyle="level4HeaderRegular"
          desktopStyle="bodyDefaultRegular"
          color={COLORS.black90}
          textAlign={ALIGN_CENTER}
        >
          <Trans
            t={t}
            i18nKey="homing_pipette_dangerous"
            values={{
              mount,
            }}
            components={{
              bold: <strong />,
            }}
          />
        </StyledText>
      </Flex>
      <RecoveryFooterButtons
        primaryBtnOnClick={primaryOnClick}
        primaryBtnTextOverride={t('begin_removal')}
        secondaryBtnOnClick={secondaryOnClick}
        secondaryBtnTextOverride={t('skip')}
        secondaryAsTertiary={true}
      />
    </RecoverySingleColumnContentWrapper>
  )
}

function DropTipFlowsContainer(
  props: RecoveryContentProps
): JSX.Element | null {
  const {
    robotType,
    tipStatusUtils,
    routeUpdateActions,
    recoveryCommands,
    currentRecoveryOptionUtils,
  } = props
  const { DROP_TIP_FLOWS, ROBOT_CANCELING, RETRY_NEW_TIPS } = RECOVERY_MAP
  const { proceedToRouteAndStep, setRobotInMotion } = routeUpdateActions
  const { selectedRecoveryOption } = currentRecoveryOptionUtils
  const { setTipStatusResolved } = tipStatusUtils
  const { cancelRun } = recoveryCommands

  const { mount, specs } = tipStatusUtils.aPipetteWithTip as PipetteWithTip // Safe as we have to have tips to get to this point in the flow.

  const onCloseFlow = (): void => {
    if (selectedRecoveryOption === RETRY_NEW_TIPS.ROUTE) {
      void proceedToRouteAndStep(
        RETRY_NEW_TIPS.ROUTE,
        RETRY_NEW_TIPS.STEPS.REPLACE_TIPS
      )
    } else {
      void setTipStatusResolved(onEmptyCache, onTipsDetected)
    }
  }

  const onEmptyCache = (): void => {
    void setRobotInMotion(true, ROBOT_CANCELING.ROUTE).then(() => {
      cancelRun()
    })
  }

  const onTipsDetected = (): void => {
    void proceedToRouteAndStep(DROP_TIP_FLOWS.ROUTE)
  }

  const fixitCommandTypeUtils = useDropTipFlowUtils(props)

  return (
    <RecoverySingleColumnContentWrapper>
      <DropTipWizardFlows
        robotType={robotType}
        closeFlow={onCloseFlow}
        mount={mount}
        instrumentModelSpecs={specs}
        fixitCommandTypeUtils={fixitCommandTypeUtils}
      />
    </RecoverySingleColumnContentWrapper>
  )
}

// Builds the overrides injected into DT Wiz.
export function useDropTipFlowUtils({
  tipStatusUtils,
  failedCommand,
  currentRecoveryOptionUtils,
  subMapUtils,
  routeUpdateActions,
  recoveryMap,
}: RecoveryContentProps): FixitCommandTypeUtils {
  const { t } = useTranslation('error_recovery')
  const {
    RETRY_NEW_TIPS,
    SKIP_STEP_WITH_NEW_TIPS,
    ERROR_WHILE_RECOVERING,
    DROP_TIP_FLOWS,
  } = RECOVERY_MAP
  const { runId } = tipStatusUtils
  const { step } = recoveryMap
  const { selectedRecoveryOption } = currentRecoveryOptionUtils
  const { proceedToRouteAndStep } = routeUpdateActions
  const { updateSubMap, subMap } = subMapUtils
  const failedCommandId = failedCommand?.id ?? '' // We should have a failed command here unless the run is not in AWAITING_RECOVERY.

  const buildTipDropCompleteBtn = (): string => {
    switch (selectedRecoveryOption) {
      case RETRY_NEW_TIPS.ROUTE:
      case SKIP_STEP_WITH_NEW_TIPS.ROUTE:
        return t('proceed_to_tip_selection')
      default:
        return t('proceed_to_cancel')
    }
  }

  const buildTipDropCompleteRouting = (): (() => void) | null => {
    const routeTo = (selectedRoute: RecoveryRoute, step: RouteStep): void => {
      void proceedToRouteAndStep(selectedRoute, step)
    }

    switch (selectedRecoveryOption) {
      case RETRY_NEW_TIPS.ROUTE:
        return () => {
          routeTo(selectedRecoveryOption, RETRY_NEW_TIPS.STEPS.REPLACE_TIPS)
        }
      case SKIP_STEP_WITH_NEW_TIPS.ROUTE:
        return () => {
          routeTo(
            selectedRecoveryOption,
            SKIP_STEP_WITH_NEW_TIPS.STEPS.REPLACE_TIPS
          )
        }
      default:
        return null
    }
  }

  const buildCopyOverrides = (): FixitCommandTypeUtils['copyOverrides'] => {
    return {
      tipDropCompleteBtnCopy: buildTipDropCompleteBtn(),
      beforeBeginningTopText: t('preserve_aspirated_liquid'),
    }
  }

  const buildErrorOverrides = (): FixitCommandTypeUtils['errorOverrides'] => {
    return {
      tipDropFailed: () => {
        return proceedToRouteAndStep(
          ERROR_WHILE_RECOVERING.ROUTE,
          ERROR_WHILE_RECOVERING.STEPS.DROP_TIP_TIP_DROP_FAILED
        )
      },
      blowoutFailed: () => {
        return proceedToRouteAndStep(
          ERROR_WHILE_RECOVERING.ROUTE,
          ERROR_WHILE_RECOVERING.STEPS.DROP_TIP_BLOWOUT_FAILED
        )
      },
      generalFailure: () =>
        proceedToRouteAndStep(
          ERROR_WHILE_RECOVERING.ROUTE,
          ERROR_WHILE_RECOVERING.STEPS.DROP_TIP_GENERAL_ERROR
        ),
    }
  }

  const buildButtonOverrides = (): FixitCommandTypeUtils['buttonOverrides'] => {
    return {
      goBackBeforeBeginning: () => {
        return proceedToRouteAndStep(DROP_TIP_FLOWS.ROUTE)
      },
      tipDropComplete: buildTipDropCompleteRouting(),
    }
  }

  // If a specific step within the DROP_TIP_FLOWS route is selected, begin the Drop Tip Flows at its related route.
  //
  // NOTE: The substep is cleared by drop tip wizard after the completion of the wizard flow.
  const buildRouteOverride = (): FixitCommandTypeUtils['routeOverride'] => {
    if (subMap?.route != null) {
      return { route: subMap.route, step: subMap.step }
    }

    switch (step) {
      case DROP_TIP_FLOWS.STEPS.CHOOSE_TIP_DROP:
        return { route: DT_ROUTES.DROP_TIP, step: subMap?.step ?? null }
      case DROP_TIP_FLOWS.STEPS.CHOOSE_BLOWOUT:
        return { route: DT_ROUTES.BLOWOUT, step: subMap?.step ?? null }
    }
  }

  return {
    runId,
    failedCommandId,
    copyOverrides: buildCopyOverrides(),
    errorOverrides: buildErrorOverrides(),
    buttonOverrides: buildButtonOverrides(),
    routeOverride: buildRouteOverride(),
    reportMap: updateSubMap,
  }
}
