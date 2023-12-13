import * as React from 'react'
import { AlertItem, OutlineButton } from '@opentrons/components'
import { i18n } from '../../localization'
// TODO: Ian 2019-03-27 the use of Component Library `Alert` is being
// stretched beyond its intentions here, we should reconcile PD + Run App uses of Alert later
import styles from './alerts.module.css'
import { AlertData, AlertType } from './types'

interface PDAlertProps {
  alertType: AlertType
  title: string
  description: AlertData['description']
  onDismiss?: (() => unknown) | null
}

export const PDAlert = (props: PDAlertProps): JSX.Element => {
  const { alertType, title, description, onDismiss } = props
  return (
    <AlertItem
      type={alertType}
      title={
        <div className={styles.alert_inner_wrapper}>
          <div className={styles.icon_label}>
            {i18n.t(`alert.type.${alertType}`)}
          </div>
          <div className={styles.alert_body}>
            <div className={styles.alert_title}>{title}</div>
            <div className={styles.alert_description}>{description}</div>
          </div>
          {onDismiss != null && (
            <OutlineButton
              className={styles.dismiss_button}
              onClick={onDismiss}
            >
              {i18n.t('alert.dismiss')}
            </OutlineButton>
          )}
        </div>
      }
    />
  )
}
