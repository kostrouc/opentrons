import * as React from 'react'
import {
  Card,
  OutlineButton,
  ToggleButton,
  LabeledValue,
} from '@opentrons/components'
import { connect } from 'react-redux'

import {
  actions as analyticsActions,
  selectors as analyticsSelectors,
} from '../../analytics'
import { OLDEST_MIGRATEABLE_VERSION } from '../../load-file/migration'
import { i18n } from '../../localization'
import {
  actions as tutorialActions,
  selectors as tutorialSelectors,
} from '../../tutorial'
import { BaseState, ThunkDispatch } from '../../types'
import { FeatureFlagCard } from './FeatureFlagCard'
import styles from './SettingsPage.css'

interface Props {
  canClearHintDismissals: boolean
  hasOptedIn: boolean | null
  restoreHints: () => unknown
  toggleOptedIn: () => unknown
}

interface SP {
  canClearHintDismissals: Props['canClearHintDismissals']
  hasOptedIn: Props['hasOptedIn']
}

function SettingsAppComponent(props: Props): JSX.Element {
  const {
    canClearHintDismissals,
    hasOptedIn,
    restoreHints,
    toggleOptedIn,
  } = props
  return (
    <>
      <div className={styles.page_row}>
        <Card title={i18n.t('card.title.information')}>
          <div className={styles.card_content}>
            <div className={styles.setting_row}>
              <LabeledValue
                className={styles.labeled_value}
                label={i18n.t('application.version')}
                value={process.env.OT_PD_VERSION || OLDEST_MIGRATEABLE_VERSION}
              />
              {/* TODO: BC 2019-02-26 add release notes link here, when there are release notes */}
            </div>
          </div>
        </Card>
      </div>
      <div className={styles.page_row}>
        <Card title={i18n.t('card.title.hints')}>
          <div className={styles.card_content}>
            <div className={styles.setting_row}>
              {i18n.t('card.body.restore_hints')}
              <OutlineButton
                className={styles.button}
                disabled={!canClearHintDismissals}
                onClick={restoreHints}
              >
                {canClearHintDismissals
                  ? i18n.t('button.restore')
                  : i18n.t('button.restored')}
              </OutlineButton>
            </div>
          </div>
        </Card>
      </div>
      <div className={styles.page_row}>
        <Card title={i18n.t('card.title.privacy')}>
          <div className={styles.card_content}>
            <div className={styles.setting_row}>
              <p className={styles.toggle_label}>
                {i18n.t('card.toggle.share_session')}
              </p>
              <ToggleButton
                className={styles.toggle_button}
                toggledOn={Boolean(hasOptedIn)}
                onClick={toggleOptedIn}
              />
            </div>

            <p className={styles.card_body}>
              {i18n.t('card.body.reason_for_collecting_data')}
            </p>
            <ul className={styles.card_point_list}>
              <li>{i18n.t('card.body.data_collected_is_internal')}</li>
              {/* TODO: BC 2018-09-26 uncomment when only using fullstory <li>{i18n.t('card.body.data_only_from_pd')}</li> */}
              <li>{i18n.t('card.body.opt_out_of_data_collection')}</li>
            </ul>
          </div>
        </Card>
      </div>
      <div className={styles.page_row}>
        <FeatureFlagCard />
      </div>
    </>
  )
}

function mapStateToProps(state: BaseState): SP {
  return {
    hasOptedIn: analyticsSelectors.getHasOptedIn(state),
    canClearHintDismissals: tutorialSelectors.getCanClearHintDismissals(state),
  }
}

function mergeProps(
  stateProps: SP,
  dispatchProps: { dispatch: ThunkDispatch<any> }
): Props {
  const { dispatch } = dispatchProps
  const { hasOptedIn } = stateProps

  const _toggleOptedIn = hasOptedIn
    ? analyticsActions.optOut
    : analyticsActions.optIn
  return {
    ...stateProps,
    toggleOptedIn: () => dispatch(_toggleOptedIn()),
    restoreHints: () => dispatch(tutorialActions.clearAllHintDismissals()),
  }
}

export const SettingsApp = connect(
  mapStateToProps,
  // @ts-expect-error(sa, 2021-6-21): TODO: refactor to use hooks api
  null,
  mergeProps
)(SettingsAppComponent)
